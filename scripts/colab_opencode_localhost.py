#!/usr/bin/env python3
"""Start Opencode in Colab and expose it at local localhost without SSH."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

from aiohttp import ClientSession, ClientTimeout, WSMsgType, web
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from websockets.sync.client import connect as websocket_connect

from colab_opencode_web_terminal import (
    DEFAULT_CWD,
    DEFAULT_DRIVE_FOLDER,
    DEFAULT_NOTEBOOK_NAME,
    DEFAULT_PORT,
    DEFAULT_REPO,
    DEFAULT_SETUP_TIMEOUT,
    DEFAULT_TERMINAL_BACKEND,
    outputs_text,
    result_payload,
    setup_cell_code,
)


DEFAULT_LOCAL_HOST = "127.0.0.1"
DEFAULT_LOCAL_PORT = 8765
HOP_BY_HOP_HEADERS = {
    "connection",
    "upgrade",
    "te",
    "trailer",
    "trailers",
    "transfer-encoding",
    "keep-alive",
    "proxy-authorization",
    "proxy-authenticate",
    "proxy-connection",
}
WEBSOCKET_HANDSHAKE_HEADERS = {
    "sec-websocket-extensions",
    "sec-websocket-key",
    "sec-websocket-protocol",
    "sec-websocket-version",
}


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def redact_url(url: str) -> str:
    return re.sub(r"(mcpProxyToken=)[^&]+", r"\1<redacted>", url)


def parse_setup_result(output: str) -> dict:
    marker = "COLAB_OPENCODE_RESULT "
    marker_index = output.find(marker)
    if marker_index >= 0:
        decoder = json.JSONDecoder()
        payload = output[marker_index + len(marker) :].lstrip()
        result, _end = decoder.raw_decode(payload)
        if not isinstance(result, dict):
            raise RuntimeError(f"Opencode setup emitted non-object result: {result!r}")
        return result
    raise RuntimeError("Opencode setup did not emit COLAB_OPENCODE_RESULT.")


def build_target_url(remote_base: str, request: web.Request, *, websocket: bool = False) -> str:
    base = remote_base.rstrip("/")
    path_qs = request.rel_url.raw_path_qs or "/"
    if not path_qs.startswith("/"):
        path_qs = "/" + path_qs
    target = base + path_qs
    if websocket:
        if target.startswith("https://"):
            target = "wss://" + target.removeprefix("https://")
        elif target.startswith("http://"):
            target = "ws://" + target.removeprefix("http://")
    return target


def filtered_request_headers(
    request: web.Request,
    extra_headers: dict[str, str] | None = None,
    excluded_headers: set[str] | None = None,
) -> dict[str, str]:
    blocked_headers = HOP_BY_HOP_HEADERS | {"host"} | (excluded_headers or set())
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in blocked_headers
    }
    headers.update(extra_headers or {})
    return headers


def filtered_response_headers(headers) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }


def requested_websocket_protocols(request: web.Request) -> tuple[str, ...]:
    protocols: list[str] = []
    for value in request.headers.getall("Sec-WebSocket-Protocol", []):
        for protocol in value.split(","):
            protocol = protocol.strip()
            if protocol and protocol not in protocols:
                protocols.append(protocol)
    return tuple(protocols)


async def proxy_websocket(
    request: web.Request,
    session: ClientSession,
    remote_base: str,
    extra_headers: dict[str, str],
) -> web.WebSocketResponse:
    protocols = requested_websocket_protocols(request)
    ws_local = web.WebSocketResponse(heartbeat=30, protocols=protocols)
    await ws_local.prepare(request)
    target = build_target_url(remote_base, request, websocket=True)
    headers = filtered_request_headers(request, extra_headers, WEBSOCKET_HANDSHAKE_HEADERS)

    async with session.ws_connect(
        target,
        headers=headers,
        heartbeat=30,
        max_msg_size=0,
        protocols=protocols,
    ) as ws_remote:
        async def local_to_remote() -> None:
            async for message in ws_local:
                if message.type == WSMsgType.TEXT:
                    await ws_remote.send_str(message.data)
                elif message.type == WSMsgType.BINARY:
                    await ws_remote.send_bytes(message.data)
                elif message.type == WSMsgType.PING:
                    await ws_remote.ping(message.data)
                elif message.type == WSMsgType.PONG:
                    await ws_remote.pong(message.data)
                elif message.type == WSMsgType.CLOSE:
                    await ws_remote.close()

        async def remote_to_local() -> None:
            async for message in ws_remote:
                if message.type == WSMsgType.TEXT:
                    await ws_local.send_str(message.data)
                elif message.type == WSMsgType.BINARY:
                    await ws_local.send_bytes(message.data)
                elif message.type == WSMsgType.PING:
                    await ws_local.ping(message.data)
                elif message.type == WSMsgType.PONG:
                    await ws_local.pong(message.data)
                elif message.type == WSMsgType.CLOSE:
                    await ws_local.close()

        done, pending = await asyncio.wait(
            {
                asyncio.create_task(local_to_remote()),
                asyncio.create_task(remote_to_local()),
            },
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        for task in done:
            task.result()
    return ws_local


async def proxy_http(
    request: web.Request,
    session: ClientSession,
    remote_base: str,
    extra_headers: dict[str, str],
) -> web.Response:
    target = build_target_url(remote_base, request)
    headers = filtered_request_headers(request, extra_headers)
    body = await request.read()
    async with session.request(
        request.method,
        target,
        headers=headers,
        data=body if body else None,
        allow_redirects=False,
    ) as response:
        response_body = await response.read()
        response_headers = filtered_response_headers(response.headers)
        return web.Response(
            body=response_body,
            status=response.status,
            reason=response.reason,
            headers=response_headers,
        )


async def make_proxy_app(remote_base: str, extra_headers: dict[str, str]) -> web.Application:
    session = ClientSession(
        timeout=ClientTimeout(total=None, sock_connect=30),
        auto_decompress=False,
    )
    app = web.Application()
    app["session"] = session

    async def handle(request: web.Request) -> web.StreamResponse:
        if request.headers.get("Upgrade", "").lower() == "websocket":
            return await proxy_websocket(request, session, remote_base, extra_headers)
        return await proxy_http(request, session, remote_base, extra_headers)

    async def cleanup(app: web.Application) -> None:
        await app["session"].close()

    app.router.add_route("*", "/{tail:.*}", handle)
    app.on_cleanup.append(cleanup)
    return app


async def start_local_proxy(
    remote_base: str,
    host: str,
    port: int,
    extra_headers: dict[str, str],
) -> web.AppRunner:
    app = await make_proxy_app(remote_base, extra_headers)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner


async def smoke_localhost(url: str) -> dict:
    async with ClientSession(timeout=ClientTimeout(total=20)) as session:
        async with session.get(url) as response:
            text = await response.text(errors="replace")
            text_lower = text.lower()
            return {
                "ok": response.status < 500
                and any(marker in text_lower for marker in ("ttyd", "opencode", "ghosttown", "ghostty")),
                "status": response.status,
                "bodyPrefix": text[:200],
            }


def cdp_json(port: int, path: str) -> dict | list:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def cdp_call(websocket_url: str, method: str, params: dict) -> dict:
    with websocket_connect(websocket_url, open_timeout=5) as ws:
        ws.send(json.dumps({"id": 1, "method": method, "params": params}))
        while True:
            message = json.loads(ws.recv())
            if message.get("id") == 1:
                if "error" in message:
                    raise RuntimeError(json.dumps(message["error"], ensure_ascii=False))
                return message.get("result", {})


def proxy_auth_headers(cdp_port: int, remote_url: str) -> tuple[dict[str, str], dict]:
    parsed = urllib.parse.urlparse(remote_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    pages = [
        target
        for target in cdp_json(cdp_port, "/json/list")
        if target.get("type") in {"page", "iframe"} and target.get("webSocketDebuggerUrl")
    ]
    target = next((item for item in pages if parsed.netloc in item.get("url", "")), None)
    target = target or next(
        (item for item in pages if "colab.research.google.com" in item.get("url", "")),
        None,
    )
    if not target:
        return {}, {"ok": False, "error": "No CDP page or iframe target found for proxy cookies."}

    result = cdp_call(
        target["webSocketDebuggerUrl"],
        "Network.getCookies",
        {"urls": [remote_url]},
    )
    cookies = result.get("cookies") or []
    if not cookies:
        return {}, {"ok": False, "error": "No browser cookies found for Colab proxy URL."}
    cookie_header = "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in cookies)
    headers = {
        "Cookie": cookie_header,
        "Origin": origin,
    }
    return headers, {
        "ok": True,
        "count": len(cookies),
        "names": sorted(str(cookie.get("name")) for cookie in cookies),
        "domains": sorted({str(cookie.get("domain")) for cookie in cookies if cookie.get("domain")}),
        "targetUrl": target.get("url"),
    }


async def open_mcp_connection(client: Client, args: argparse.Namespace) -> dict:
    opened = result_payload(
        await client.call_tool(
            "open_colab_browser_connection",
            {},
            timeout=args.connection_timeout + 60,
            raise_on_error=False,
        )
    )
    info = result_payload(await client.call_tool("get_connection_info", {}, timeout=60, raise_on_error=False))
    if not info.get("connected"):
        raise RuntimeError(f"Colab MCP did not connect: opened={opened} info={info}")
    return info


async def connect_runtime(client: Client, args: argparse.Namespace) -> dict:
    if args.skip_runtime_connect:
        return {"skipped": True}
    payload = result_payload(
        await client.call_tool(
            "connect_runtime",
            {"waitSeconds": args.runtime_timeout},
            timeout=args.runtime_timeout + 90,
            raise_on_error=False,
        )
    )
    if not payload.get("ok"):
        raise RuntimeError(f"Colab runtime did not connect: {payload}")
    return payload


async def setup_opencode(client: Client, args: argparse.Namespace) -> dict:
    code = setup_cell_code(
        port=args.colab_port,
        cwd=args.cwd,
        install_timeout=args.install_timeout,
        drive_persistence=args.drive_persistence,
        drive_folder=args.drive_folder,
        notebook_name=args.notebook_name,
        require_drive=args.require_drive,
        drive_mount_timeout=args.drive_mount_timeout,
        terminal_backend=args.terminal_backend,
    )
    add = result_payload(
        await client.call_tool(
            "add_code_cell",
            {"cellIndex": 0, "language": "python", "code": code},
            timeout=60,
            raise_on_error=False,
        )
    )
    cell_id = add.get("newCellId") or add.get("cellId")
    if not cell_id:
        raise RuntimeError(f"Could not create Opencode setup cell: {add}")
    run = result_payload(
        await client.call_tool(
            "run_code_cell",
            {"cellId": cell_id},
            timeout=args.setup_timeout,
            raise_on_error=False,
        )
    )
    output = outputs_text(run)
    print(output, end="" if output.endswith("\n") else "\n", flush=True)
    result = parse_setup_result(output)
    if not result.get("ok") or not result.get("portOpen"):
        raise RuntimeError(f"Opencode setup failed: {result}")
    if not result.get("proxyUrl"):
        raise RuntimeError(f"Opencode setup did not return a Colab proxy URL: {result}")
    return result


def build_mcp_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    values = {
        "COLAB_MCP_BROWSER_COMMAND": args.browser_command,
        "COLAB_MCP_BROWSER_USER_DATA_DIR": args.browser_user_data_dir,
        "COLAB_MCP_BROWSER_PROFILE": args.browser_profile,
        "COLAB_MCP_BROWSER_HEADLESS": "1" if args.browser_headless else "0",
        "COLAB_MCP_BROWSER_COPY_PROFILE": "1" if args.browser_copy_profile else "0",
        "COLAB_MCP_BROWSER_PROFILE_COPY_DIR": args.browser_profile_copy_dir,
        "COLAB_MCP_BROWSER_COOKIE_FILE": args.browser_cookie_file,
        "COLAB_MCP_EDGE_CDP_PORT": str(args.cdp_port),
        "COLAB_MCP_CONNECTION_TIMEOUT": str(args.connection_timeout),
    }
    for key, value in values.items():
        if value not in (None, ""):
            env[key] = str(value)
    return env


async def run(args: argparse.Namespace) -> None:
    env = build_mcp_env(args)
    transport = StdioTransport(
        command="uv",
        args=["run", "colab-mcp"],
        cwd=str(args.repo),
        env=env,
        log_file=Path(args.log_file),
    )
    async with Client(transport, init_timeout=90, timeout=args.setup_timeout + 300) as client:
        print("Connecting Colab MCP browser session...", flush=True)
        info = await open_mcp_connection(client, args)
        print(f"Connected to Colab MCP. Browser connected={info.get('connected')}", flush=True)
        runtime = await connect_runtime(client, args)
        print(f"Runtime status: {json.dumps(runtime, sort_keys=True)[:1000]}", flush=True)
        setup = await setup_opencode(client, args)

    remote_url = str(setup["proxyUrl"]).rstrip("/")
    local_url = f"http://{args.local_host}:{args.local_port}"
    extra_headers, cookie_summary = proxy_auth_headers(args.cdp_port, remote_url)
    print(f"Colab proxy auth cookies: {json.dumps(cookie_summary, sort_keys=True)}", flush=True)
    runner = await start_local_proxy(remote_url, args.local_host, args.local_port, extra_headers)
    print(f"Opencode backend: {setup.get('terminalBackend')}", flush=True)
    print(f"Opencode workdir: {setup.get('workdir')}", flush=True)
    print(f"Opencode recovery files: {json.dumps(setup.get('recoveryFiles') or [])}", flush=True)
    print(f"Opencode Colab proxy URL: {remote_url}", flush=True)
    print(f"Localhost URL: {local_url}", flush=True)
    if setup.get("terminalBackend") == "ghosttown":
        print(f"Ghost Town new Opencode session URL: {local_url}/new", flush=True)
    try:
        smoke = await smoke_localhost(local_url)
    except Exception:
        await runner.cleanup()
        raise
    print(f"Localhost smoke: {json.dumps(smoke, sort_keys=True)}", flush=True)
    if not smoke.get("ok"):
        await runner.cleanup()
        raise RuntimeError(f"Localhost smoke failed: {smoke}")
    if args.exit_after_smoke:
        await runner.cleanup()
        return
    print("Local proxy is running. Press Ctrl+C to stop.", flush=True)
    stop = asyncio.Event()
    try:
        await stop.wait()
    finally:
        await runner.cleanup()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Opencode in Colab and expose its web terminal at local localhost without SSH."
    )
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--browser-command", default=os.environ.get("COLAB_MCP_BROWSER_COMMAND", "google-chrome-stable"))
    parser.add_argument("--browser-user-data-dir", default=os.environ.get("COLAB_MCP_BROWSER_USER_DATA_DIR", "/home/astra/.config/google-chrome"))
    parser.add_argument("--browser-profile", default=os.environ.get("COLAB_MCP_BROWSER_PROFILE", "Default"))
    parser.add_argument(
        "--browser-headless",
        action=argparse.BooleanOptionalAction,
        default=env_bool("COLAB_MCP_BROWSER_HEADLESS", True),
    )
    parser.add_argument(
        "--browser-copy-profile",
        action=argparse.BooleanOptionalAction,
        default=env_bool("COLAB_MCP_BROWSER_COPY_PROFILE", True),
    )
    parser.add_argument(
        "--browser-profile-copy-dir",
        default=os.environ.get("COLAB_MCP_BROWSER_PROFILE_COPY_DIR", "/tmp/colab-mcp-opencode-profile-copy"),
    )
    parser.add_argument("--browser-cookie-file", default=os.environ.get("COLAB_MCP_BROWSER_COOKIE_FILE"))
    parser.add_argument("--cdp-port", type=int, default=int(os.environ.get("COLAB_MCP_EDGE_CDP_PORT", "9458")))
    parser.add_argument("--connection-timeout", type=int, default=int(os.environ.get("COLAB_MCP_CONNECTION_TIMEOUT", "240")))
    parser.add_argument("--runtime-timeout", type=int, default=180)
    parser.add_argument("--skip-runtime-connect", action="store_true")
    parser.add_argument("--setup-timeout", type=int, default=DEFAULT_SETUP_TIMEOUT)
    parser.add_argument("--install-timeout", type=int, default=600)
    parser.add_argument("--colab-port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--cwd", default=os.environ.get("COLAB_OPENCODE_CWD", DEFAULT_CWD))
    parser.add_argument(
        "--terminal-backend",
        choices=("ttyd", "ghosttown"),
        default=os.environ.get("COLAB_OPENCODE_TERMINAL_BACKEND", DEFAULT_TERMINAL_BACKEND),
    )
    parser.add_argument(
        "--drive-persistence",
        action=argparse.BooleanOptionalAction,
        default=env_bool("COLAB_OPENCODE_DRIVE_PERSISTENCE", True),
    )
    parser.add_argument("--drive-folder", default=os.environ.get("COLAB_OPENCODE_DRIVE_FOLDER", DEFAULT_DRIVE_FOLDER))
    parser.add_argument("--notebook-name", default=os.environ.get("COLAB_OPENCODE_NOTEBOOK_NAME", DEFAULT_NOTEBOOK_NAME))
    parser.add_argument(
        "--require-drive",
        action=argparse.BooleanOptionalAction,
        default=env_bool("COLAB_OPENCODE_REQUIRE_DRIVE", True),
    )
    parser.add_argument(
        "--drive-mount-timeout",
        type=int,
        default=int(os.environ.get("COLAB_OPENCODE_DRIVE_MOUNT_TIMEOUT", "180")),
    )
    parser.add_argument("--local-host", default=DEFAULT_LOCAL_HOST)
    parser.add_argument("--local-port", type=int, default=DEFAULT_LOCAL_PORT)
    parser.add_argument("--exit-after-smoke", action="store_true")
    parser.add_argument("--log-file", default="/tmp/colab-mcp-opencode-localhost.log")
    args = parser.parse_args()
    if not (1 <= args.local_port <= 65535):
        parser.error("--local-port must be between 1 and 65535")
    if not (1 <= args.colab_port <= 65535):
        parser.error("--colab-port must be between 1 and 65535")
    if args.drive_mount_timeout <= 0:
        parser.error("--drive-mount-timeout must be greater than 0")
    if args.drive_persistence and not args.drive_folder:
        parser.error("--drive-folder is required when drive persistence is enabled")
    if args.drive_persistence and not args.notebook_name.endswith(".ipynb"):
        parser.error("--notebook-name must end with .ipynb")
    return args


def main() -> None:
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
