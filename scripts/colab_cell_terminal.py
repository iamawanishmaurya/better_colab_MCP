#!/usr/bin/env python3
"""Interactive tmux-friendly shell bridge backed by Colab code cells."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from colab_visible_connect import visible_connect_attempt


DEFAULT_REPO = Path(__file__).resolve().parents[1]
DEFAULT_CWD = "/content"
DEFAULT_CONNECTION_TIMEOUT = 600
DEFAULT_CONNECT_POLL_INTERVAL = 2
DEFAULT_CONNECT_STATUS_INTERVAL = 15


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


def command_cell_code(command: str, cwd: str) -> str:
    script = (
        f"cd {shlex.quote(cwd)} && "
        "{ "
        f"{command}; "
        "rc=$?; "
        "printf '\\n__COLAB_MCP_EXIT__%s\\n' \"$rc\"; "
        "printf '__COLAB_MCP_PWD__%s\\n' \"$PWD\"; "
        "}"
    )
    return (
        "# COLAB_MCP_TMUX_CELL_TERMINAL\n"
        "import subprocess, sys\n"
        f"script = {script!r}\n"
        "proc = subprocess.run(\n"
        "    script,\n"
        "    shell=True,\n"
        "    executable='/bin/bash',\n"
        "    text=True,\n"
        "    capture_output=True,\n"
        ")\n"
        "if proc.stdout:\n"
        "    print(proc.stdout, end='')\n"
        "if proc.stderr:\n"
        "    print(proc.stderr, file=sys.stderr, end='')\n"
    )


def parse_terminal_output(text: str, current_cwd: str) -> tuple[str, str, int | None]:
    exit_code = None
    cwd = current_cwd
    exit_match = re.search(r"\n?__COLAB_MCP_EXIT__(-?\d+)\n", text)
    if exit_match:
        exit_code = int(exit_match.group(1))
    cwd_match = re.search(r"__COLAB_MCP_PWD__(.+)\n?", text)
    if cwd_match:
        cwd = cwd_match.group(1).strip() or cwd
    text = re.sub(r"\n?__COLAB_MCP_EXIT__-?\d+\n", "\n", text)
    text = re.sub(r"__COLAB_MCP_PWD__.+\n?", "", text)
    return text.rstrip("\n"), cwd, exit_code


def redact_url(url: str) -> str:
    return re.sub(r"(mcpProxyToken=)[^&]+", r"\1<redacted>", url)


async def connect_browser(client: Client, args: argparse.Namespace) -> bool:
    info = result_payload(await client.call_tool("get_connection_info", {}))
    scratch_url = info["scratchUrl"]
    open_command = [args.browser_command]
    if args.browser_open_mode == "new-window":
        open_command.append("--new-window")
    elif args.browser_open_mode == "new-tab":
        open_command.append("--new-tab")
    open_command.append(scratch_url)
    subprocess.Popen(
        open_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    display_url = scratch_url if args.print_url else redact_url(scratch_url)
    print(f"Opened Colab scratch URL with {args.browser_command}.", flush=True)
    print(f"Connection URL: {display_url}", flush=True)

    start = time.monotonic()
    next_status = start
    next_auto_connect = start + args.auto_click_delay
    auto_connect_attempts = 0
    while True:
        elapsed = int(time.monotonic() - start)
        if elapsed >= args.connection_timeout:
            return False
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
        if time.monotonic() >= next_status:
            print(
                "Waiting for browser MCP connection "
                f"({elapsed}s/{args.connection_timeout}s)...",
                flush=True,
            )
            next_status = time.monotonic() + args.connect_status_interval
        await asyncio.sleep(args.connect_poll_interval)
        info = result_payload(await client.call_tool("get_connection_info", {}))
        if info.get("connected"):
            return True


async def create_terminal_cell(client: Client) -> str:
    payload = result_payload(
        await client.call_tool(
            "add_code_cell",
            {
                "cellIndex": 0,
                "language": "python",
                "code": "# COLAB_MCP_TMUX_CELL_TERMINAL\nprint('ready')",
            },
            timeout=60,
            raise_on_error=False,
        )
    )
    cell_id = payload.get("newCellId") or payload.get("cellId")
    if not cell_id:
        raise RuntimeError(f"Could not create terminal cell: {payload}")
    return str(cell_id)


async def run_command(client: Client, cell_id: str, command: str, cwd: str) -> tuple[str, str, int | None]:
    await client.call_tool(
        "update_cell",
        {"cellId": cell_id, "content": command_cell_code(command, cwd)},
        timeout=60,
        raise_on_error=False,
    )
    run = await client.call_tool(
        "run_code_cell",
        {"cellId": cell_id},
        timeout=300,
        raise_on_error=False,
    )
    output, next_cwd, exit_code = parse_terminal_output(outputs_text(result_payload(run)), cwd)
    return output, next_cwd, exit_code


async def repl(args: argparse.Namespace) -> None:
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
    async with Client(transport, init_timeout=45, timeout=300) as client:
        print("Connecting Colab MCP browser session...", flush=True)
        connected = await connect_browser(client, args)
        if not connected:
            raise RuntimeError(
                "Browser did not connect to the MCP server. "
                "If Chrome did not open the scratch notebook, rerun with --print-url "
                "and open the printed URL manually in the intended Google profile."
            )
        print("Connected. Creating terminal cell...", flush=True)
        cell_id = await create_terminal_cell(client)
        cwd = args.cwd
        print(f"Ready. Backing Colab cell: {cell_id}", flush=True)
        print("Type shell commands. Use 'exit' or 'quit' to close this bridge.", flush=True)
        while True:
            line = await asyncio.to_thread(input, f"colab:{cwd}$ ")
            command = line.strip()
            if not command:
                continue
            if command in {"exit", "quit"}:
                return
            if command == "help":
                print("Run shell commands in Colab through a reusable code cell. Builtins: help, exit, quit.")
                continue
            try:
                output, cwd, exit_code = await run_command(client, cell_id, command, cwd)
                if output:
                    print(output)
                if exit_code not in (0, None):
                    print(f"[exit {exit_code}]")
            except Exception as exc:
                print(f"[bridge error] {exc}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open a tmux-friendly shell backed by Colab MCP code cells.")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--browser-command", default=os.environ.get("COLAB_MCP_BROWSER_COMMAND", "google-chrome-stable"))
    parser.add_argument("--browser-user-data-dir", default=os.environ.get("COLAB_MCP_BROWSER_USER_DATA_DIR", "/home/astra/.config/google-chrome"))
    parser.add_argument("--browser-profile", default=os.environ.get("COLAB_MCP_BROWSER_PROFILE", "Default"))
    parser.add_argument(
        "--browser-open-mode",
        choices=("new-window", "new-tab", "current"),
        default=os.environ.get("COLAB_MCP_BROWSER_OPEN_MODE", "new-window"),
        help="How to ask the browser to open the Colab scratch URL.",
    )
    parser.add_argument(
        "--connection-timeout",
        type=int,
        default=int(os.environ.get("COLAB_MCP_CONNECTION_TIMEOUT", str(DEFAULT_CONNECTION_TIMEOUT))),
    )
    parser.add_argument(
        "--connect-poll-interval",
        type=int,
        default=int(os.environ.get("COLAB_MCP_CONNECT_POLL_INTERVAL", str(DEFAULT_CONNECT_POLL_INTERVAL))),
    )
    parser.add_argument(
        "--connect-status-interval",
        type=int,
        default=int(os.environ.get("COLAB_MCP_CONNECT_STATUS_INTERVAL", str(DEFAULT_CONNECT_STATUS_INTERVAL))),
    )
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
    parser.add_argument("--cwd", default=DEFAULT_CWD)
    parser.add_argument("--log-file", default="/tmp/colab-mcp-cell-terminal.log")
    args = parser.parse_args()
    if args.connection_timeout <= 0:
        parser.error("--connection-timeout must be greater than 0")
    if args.connect_poll_interval <= 0:
        parser.error("--connect-poll-interval must be greater than 0")
    if args.connect_status_interval <= 0:
        parser.error("--connect-status-interval must be greater than 0")
    if args.auto_click_delay < 0:
        parser.error("--auto-click-delay must be greater than or equal to 0")
    if args.auto_click_interval <= 0:
        parser.error("--auto-click-interval must be greater than 0")
    if args.auto_click_attempts < 0:
        parser.error("--auto-click-attempts must be greater than or equal to 0")
    return args


def main() -> None:
    asyncio.run(repl(parse_args()))


if __name__ == "__main__":
    main()
