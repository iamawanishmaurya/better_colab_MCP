#!/usr/bin/env python3
"""Install Opencode in Colab and expose it through a ttyd web terminal."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import subprocess
import time

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from colab_visible_connect import visible_connect_attempt


DEFAULT_REPO = Path(__file__).resolve().parents[1]
DEFAULT_CONNECTION_TIMEOUT = 600
DEFAULT_SETUP_TIMEOUT = 900
DEFAULT_PORT = 7681


def result_text(result) -> str:
    return "\n".join(
        getattr(item, "text", "")
        for item in (result.content or [])
        if getattr(item, "text", "")
    )


def result_payload(result) -> dict:
    if result.structured_content:
        return result.structured_content
    text = result_text(result)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def outputs_text(payload: dict) -> str:
    chunks: list[str] = []
    for output in payload.get("outputs", []):
        text = output.get("text", "")
        if isinstance(text, list):
            chunks.append("".join(str(part) for part in text))
        elif text:
            chunks.append(str(text))
        data = output.get("data", {})
        text_plain = data.get("text/plain") if isinstance(data, dict) else None
        if isinstance(text_plain, list):
            chunks.append("".join(str(part) for part in text_plain))
        elif text_plain:
            chunks.append(str(text_plain))
        if output.get("output_type") == "error":
            traceback = output.get("traceback") or []
            chunks.append("\n".join(str(line) for line in traceback))
    return "".join(chunks)


def redact_url(url: str) -> str:
    return re.sub(r"(mcpProxyToken=)[^&]+", r"\1<redacted>", url)


def setup_cell_code(*, port: int, cwd: str, install_timeout: int) -> str:
    return f"""
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import socket
import subprocess
import time
import urllib.request

PORT = {port!r}
WORKDIR = {cwd!r}
INSTALL_TIMEOUT = {install_timeout!r}
LOG_PATH = "/content/opencode-ttyd.log"
PID_PATH = "/content/opencode-ttyd.pid"


def emit(message):
    print(message, flush=True)


def run(command, *, timeout=300, check=True):
    emit("$ " + command)
    completed = subprocess.run(
        command,
        shell=True,
        executable="/bin/bash",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    output = completed.stdout or ""
    if len(output) > 12000:
        emit(output[-12000:])
    else:
        emit(output)
    if check and completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit {{completed.returncode}}: {{command}}")
    return completed


def install_opencode():
    os.environ["PATH"] = os.path.expanduser("~/.opencode/bin") + os.pathsep + os.environ.get("PATH", "")
    if shutil.which("opencode"):
        emit("opencode already installed: " + shutil.which("opencode"))
        return
    run(
        "curl -fsSL --connect-timeout 20 --max-time "
        + str(INSTALL_TIMEOUT)
        + " https://opencode.ai/install | bash -s -- --no-modify-path",
        timeout=INSTALL_TIMEOUT + 60,
    )
    os.environ["PATH"] = os.path.expanduser("~/.opencode/bin") + os.pathsep + os.environ.get("PATH", "")
    if not shutil.which("opencode"):
        raise RuntimeError("opencode was not found on PATH after installation")


def install_ttyd_from_release():
    emit("Installing ttyd from GitHub release binary")
    with urllib.request.urlopen("https://api.github.com/repos/tsl0922/ttyd/releases/latest", timeout=30) as response:
        release = json.loads(response.read().decode("utf-8"))
    machine = platform.machine().lower()
    wanted = "ttyd.x86_64" if machine in {{"x86_64", "amd64"}} else "ttyd.aarch64"
    assets = release.get("assets") or []
    asset = next((item for item in assets if item.get("name") == wanted), None)
    if not asset:
        names = ", ".join(str(item.get("name")) for item in assets)
        raise RuntimeError(f"Could not find ttyd release asset {{wanted}}. Available assets: {{names}}")
    target = "/usr/local/bin/ttyd"
    urllib.request.urlretrieve(asset["browser_download_url"], target)
    os.chmod(target, 0o755)


def install_ttyd():
    if shutil.which("ttyd"):
        emit("ttyd already installed: " + shutil.which("ttyd"))
        return
    apt = run(
        "apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -y ttyd",
        timeout=600,
        check=False,
    )
    if apt.returncode != 0 or not shutil.which("ttyd"):
        install_ttyd_from_release()
    if not shutil.which("ttyd"):
        raise RuntimeError("ttyd was not found on PATH after installation")


def port_open(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", int(port))) == 0


def start_ttyd():
    Path(WORKDIR).mkdir(parents=True, exist_ok=True)
    run(f"fuser -k {{PORT}}/tcp >/dev/null 2>&1 || true", timeout=20, check=False)
    launch = (
        "export PATH=$HOME/.opencode/bin:$PATH; "
        + "cd "
        + shlex.quote(WORKDIR)
        + "; "
        + "exec opencode"
    )
    command = (
        "nohup ttyd -W -p "
        + str(PORT)
        + " -t titleFixed=OpenCode-Colab "
        + "/bin/bash -lc "
        + shlex.quote(launch)
        + " > "
        + shlex.quote(LOG_PATH)
        + " 2>&1 & echo $! > "
        + shlex.quote(PID_PATH)
    )
    run(command, timeout=30)
    deadline = time.time() + 30
    while time.time() < deadline:
        if port_open(PORT):
            return
        time.sleep(1)
    tail = Path(LOG_PATH).read_text(errors="replace")[-4000:] if Path(LOG_PATH).exists() else ""
    raise RuntimeError("ttyd did not open the requested port. Log tail:\\n" + tail)


install_opencode()
install_ttyd()
run("opencode --version", timeout=60)
run("ttyd --version", timeout=60)
start_ttyd()

proxy_url = None
proxy_url_error = None
try:
    from google.colab import output

    try:
        proxy_url = output.eval_js(f"google.colab.kernel.proxyPort({{PORT}})")
    except Exception as exc:
        proxy_url_error = repr(exc)
    output.serve_kernel_port_as_window(PORT)
    output.serve_kernel_port_as_iframe(PORT, width="100%", height=900)
except Exception as exc:
    emit("Colab port exposure warning: " + repr(exc))
    proxy_url_error = proxy_url_error or repr(exc)

pid = Path(PID_PATH).read_text().strip() if Path(PID_PATH).exists() else ""
result = {{
    "ok": True,
    "port": PORT,
    "pid": pid,
    "workdir": WORKDIR,
    "logPath": LOG_PATH,
    "pidPath": PID_PATH,
    "opencode": shutil.which("opencode"),
    "ttyd": shutil.which("ttyd"),
    "portOpen": port_open(PORT),
    "proxyUrl": proxy_url,
    "proxyUrlError": proxy_url_error,
}}
emit("COLAB_OPENCODE_RESULT " + json.dumps(result, sort_keys=True))
"""


async def connect_browser(client: Client, args: argparse.Namespace) -> None:
    info = result_payload(await client.call_tool("get_connection_info", {}))
    scratch_url = info["scratchUrl"]
    command = [args.browser_command]
    if args.browser_open_mode == "new-window":
        command.append("--new-window")
    elif args.browser_open_mode == "new-tab":
        command.append("--new-tab")
    command.append(scratch_url)
    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    display_url = scratch_url if args.print_url else redact_url(scratch_url)
    print(f"Opened Colab scratch URL with {args.browser_command}.", flush=True)
    print(f"Connection URL: {display_url}", flush=True)

    start = time.monotonic()
    next_auto_connect = start + args.auto_click_delay
    auto_connect_attempts = 0
    while time.monotonic() - start < args.connection_timeout:
        await asyncio.sleep(args.connect_poll_interval)
        info = result_payload(await client.call_tool("get_connection_info", {}))
        elapsed = int(time.monotonic() - start)
        print(f"connected={bool(info.get('connected'))} elapsed={elapsed}s", flush=True)
        if info.get("connected"):
            return
        if (
            args.auto_click_connect
            and auto_connect_attempts < args.auto_click_attempts
            and time.monotonic() >= next_auto_connect
        ):
            result = visible_connect_attempt(
                attempt_index=auto_connect_attempts,
                title_filter=args.auto_click_window_title,
                target_url=scratch_url,
            )
            auto_connect_attempts += 1
            next_auto_connect = time.monotonic() + args.auto_click_interval
            print(f"Visible MCP auto-connect attempt {auto_connect_attempts}: {result.as_log()}", flush=True)
    raise RuntimeError("Browser did not connect to the MCP server.")


async def run_setup(args: argparse.Namespace) -> None:
    env = os.environ.copy()
    env.update(
        {
            "COLAB_MCP_BROWSER_COMMAND": args.browser_command,
            "COLAB_MCP_BROWSER_USER_DATA_DIR": args.browser_user_data_dir,
            "COLAB_MCP_BROWSER_PROFILE": args.browser_profile,
            "COLAB_MCP_CONNECTION_TIMEOUT": str(args.connection_timeout),
        }
    )
    transport = StdioTransport(
        command="uv",
        args=["run", "colab-mcp"],
        cwd=str(args.repo),
        env=env,
        log_file=Path(args.log_file),
    )
    async with Client(transport, init_timeout=45, timeout=args.setup_timeout + 180) as client:
        await connect_browser(client, args)
        code = setup_cell_code(
            port=args.port,
            cwd=args.cwd,
            install_timeout=args.install_timeout,
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
        print(f"Running Opencode setup cell: {cell_id}", flush=True)
        run = result_payload(
            await client.call_tool(
                "run_code_cell",
                {"cellId": cell_id},
                timeout=args.setup_timeout,
                raise_on_error=False,
            )
        )
        output = outputs_text(run)
        print(output, end="" if output.endswith("\n") else "\n")
        if "COLAB_OPENCODE_RESULT" not in output:
            raise RuntimeError("Opencode setup did not report success. Check output above.")
        print("Opencode web terminal is running in Colab.", flush=True)
        print(f"Open the Colab output iframe/window on port {args.port}.", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Opencode in Colab and expose it through a ttyd web terminal."
    )
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--browser-command", default=os.environ.get("COLAB_MCP_BROWSER_COMMAND", "google-chrome-stable"))
    parser.add_argument("--browser-user-data-dir", default=os.environ.get("COLAB_MCP_BROWSER_USER_DATA_DIR", "/home/astra/.config/google-chrome"))
    parser.add_argument("--browser-profile", default=os.environ.get("COLAB_MCP_BROWSER_PROFILE", "Default"))
    parser.add_argument(
        "--browser-open-mode",
        choices=("new-window", "new-tab", "current"),
        default=os.environ.get("COLAB_MCP_BROWSER_OPEN_MODE", "new-window"),
    )
    parser.add_argument("--connection-timeout", type=int, default=int(os.environ.get("COLAB_MCP_CONNECTION_TIMEOUT", str(DEFAULT_CONNECTION_TIMEOUT))))
    parser.add_argument("--connect-poll-interval", type=int, default=int(os.environ.get("COLAB_MCP_CONNECT_POLL_INTERVAL", "3")))
    parser.add_argument("--setup-timeout", type=int, default=DEFAULT_SETUP_TIMEOUT)
    parser.add_argument("--install-timeout", type=int, default=600)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--cwd", default="/content")
    parser.add_argument("--print-url", action="store_true", default=os.environ.get("COLAB_MCP_PRINT_CONNECTION_URL") == "1")
    parser.add_argument(
        "--auto-click-connect",
        action=argparse.BooleanOptionalAction,
        default=os.environ.get("COLAB_MCP_AUTO_CLICK_CONNECT", "1").strip().lower()
        not in {"0", "false", "no", "off"},
        help="Use visible-browser key automation to accept Colab's local MCP Connect dialog when CDP is unavailable.",
    )
    parser.add_argument("--auto-click-delay", type=int, default=int(os.environ.get("COLAB_MCP_AUTO_CLICK_DELAY", "8")))
    parser.add_argument("--auto-click-interval", type=int, default=int(os.environ.get("COLAB_MCP_AUTO_CLICK_INTERVAL", "8")))
    parser.add_argument("--auto-click-attempts", type=int, default=int(os.environ.get("COLAB_MCP_AUTO_CLICK_ATTEMPTS", "4")))
    parser.add_argument("--auto-click-window-title", default=os.environ.get("COLAB_MCP_AUTO_CLICK_WINDOW_TITLE", "Colab"))
    parser.add_argument("--log-file", default="/tmp/colab-mcp-opencode-web-terminal.log")
    args = parser.parse_args()
    if args.connection_timeout <= 0:
        parser.error("--connection-timeout must be greater than 0")
    if args.connect_poll_interval <= 0:
        parser.error("--connect-poll-interval must be greater than 0")
    if args.setup_timeout <= 0:
        parser.error("--setup-timeout must be greater than 0")
    if args.install_timeout <= 0:
        parser.error("--install-timeout must be greater than 0")
    if not (1 <= args.port <= 65535):
        parser.error("--port must be between 1 and 65535")
    if args.auto_click_delay < 0:
        parser.error("--auto-click-delay must be greater than or equal to 0")
    if args.auto_click_interval <= 0:
        parser.error("--auto-click-interval must be greater than 0")
    if args.auto_click_attempts < 0:
        parser.error("--auto-click-attempts must be greater than or equal to 0")
    return args


def main() -> None:
    asyncio.run(run_setup(parse_args()))


if __name__ == "__main__":
    main()
