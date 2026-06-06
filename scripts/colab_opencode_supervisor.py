#!/usr/bin/env python3
"""Supervise the Colab Opencode localhost bridge and reconnect on Enter."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from aiohttp import ClientSession, ClientTimeout

from colab_opencode_localhost import DEFAULT_LOCAL_HOST, DEFAULT_LOCAL_PORT
from colab_opencode_web_terminal import (
    DEFAULT_CWD,
    DEFAULT_DRIVE_FOLDER,
    DEFAULT_NOTEBOOK_NAME,
    DEFAULT_PORT,
    DEFAULT_REPO,
    DEFAULT_SETUP_TIMEOUT,
    DEFAULT_TERMINAL_BACKEND,
    env_bool,
)


DEFAULT_STATE_FILE = Path("/tmp/colab-mcp-opencode-session-state.json")
DEFAULT_LOG_FILE = Path("/tmp/colab-mcp-opencode-supervised-bridge.log")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_state(args: argparse.Namespace, **updates) -> None:
    state = {}
    if args.state_file.exists():
        try:
            existing = json.loads(args.state_file.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                state.update(existing)
        except json.JSONDecodeError:
            pass
    state.update({
        "updatedAt": utc_now(),
        "localUrl": f"http://{args.local_host}:{args.local_port}",
        "localHost": args.local_host,
        "localPort": args.local_port,
        "cdpPort": args.cdp_port,
        "colabPort": args.colab_port,
        "stateFile": str(args.state_file),
        "bridgeLogFile": str(args.bridge_log_file),
        "terminalBackend": args.terminal_backend,
        "drivePersistence": args.drive_persistence,
        "driveFolder": args.drive_folder,
    })
    state.update(updates)
    state["updatedAt"] = utc_now()
    args.state_file.parent.mkdir(parents=True, exist_ok=True)
    args.state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bridge_command(args: argparse.Namespace) -> list[str]:
    script = Path(__file__).resolve().with_name("colab_opencode_localhost.py")
    command = [
        sys.executable,
        str(script),
        "--repo",
        str(args.repo),
        "--browser-command",
        args.browser_command,
        "--browser-user-data-dir",
        args.browser_user_data_dir,
        "--browser-profile",
        args.browser_profile,
        "--browser-profile-copy-dir",
        args.browser_profile_copy_dir,
        "--cdp-port",
        str(args.cdp_port),
        "--connection-timeout",
        str(args.connection_timeout),
        "--runtime-timeout",
        str(args.runtime_timeout),
        "--setup-timeout",
        str(args.setup_timeout),
        "--install-timeout",
        str(args.install_timeout),
        "--colab-port",
        str(args.colab_port),
        "--cwd",
        args.cwd,
        "--terminal-backend",
        args.terminal_backend,
        "--drive-folder",
        args.drive_folder,
        "--notebook-name",
        args.notebook_name,
        "--drive-mount-timeout",
        str(args.drive_mount_timeout),
        "--local-host",
        args.local_host,
        "--local-port",
        str(args.local_port),
        "--log-file",
        args.mcp_log_file,
    ]
    command.append("--browser-headless" if args.browser_headless else "--no-browser-headless")
    command.append("--browser-copy-profile" if args.browser_copy_profile else "--no-browser-copy-profile")
    command.append("--drive-persistence" if args.drive_persistence else "--no-drive-persistence")
    command.append("--require-drive" if args.require_drive else "--no-require-drive")
    if args.browser_cookie_file:
        command.extend(["--browser-cookie-file", args.browser_cookie_file])
    if args.skip_runtime_connect:
        command.append("--skip-runtime-connect")
    return command


async def health_check(args: argparse.Namespace) -> dict:
    local_url = f"http://{args.local_host}:{args.local_port}"
    websocket_url = f"ws://{args.local_host}:{args.local_port}/ws"
    result = {
        "ok": False,
        "httpOk": False,
        "websocketOk": False,
        "checkedAt": utc_now(),
    }
    timeout = ClientTimeout(total=args.health_timeout)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.get(local_url) as response:
                text = await response.text(errors="replace")
                result["httpStatus"] = response.status
                result["httpOk"] = response.status == 200 and "ttyd" in text.lower()
            if args.check_websocket and args.terminal_backend == "ttyd":
                async with session.ws_connect(
                    websocket_url,
                    heartbeat=15,
                    max_msg_size=0,
                    protocols=("tty",),
                ):
                    result["websocketOk"] = True
            else:
                result["websocketOk"] = True
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["ok"] = bool(result["httpOk"] and result["websocketOk"])
    return result


def process_alive(process: subprocess.Popen | None) -> bool:
    return bool(process and process.poll() is None)


async def wait_for_enter(prompt: str) -> None:
    print(prompt, flush=True)
    await asyncio.to_thread(sys.stdin.readline)


async def start_bridge(args: argparse.Namespace, restart_count: int) -> subprocess.Popen:
    args.bridge_log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = args.bridge_log_file.open("a", encoding="utf-8")
    command = bridge_command(args)
    print("Reconnecting Colab MCP and Opencode...", flush=True)
    print(f"Bridge log: {args.bridge_log_file}", flush=True)
    write_state(
        args,
        status="starting",
        childPid=None,
        restartCount=restart_count,
        command=command,
        lastError=None,
    )
    process = subprocess.Popen(
        command,
        cwd=str(args.repo),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    write_state(args, status="starting", childPid=process.pid, restartCount=restart_count)
    return process


def stop_bridge(process: subprocess.Popen | None) -> None:
    if not process_alive(process):
        return
    assert process is not None
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return


async def wait_until_healthy(
    args: argparse.Namespace,
    process: subprocess.Popen,
    restart_count: int,
) -> tuple[bool, dict]:
    deadline = time.monotonic() + args.startup_timeout
    last_health: dict = {"ok": False, "error": "health check did not run"}
    while time.monotonic() < deadline:
        if process.poll() is not None:
            last_health = {"ok": False, "error": f"bridge exited with code {process.returncode}"}
            break
        last_health = await health_check(args)
        write_state(
            args,
            status="running" if last_health.get("ok") else "starting",
            childPid=process.pid,
            restartCount=restart_count,
            lastHealth=last_health,
        )
        if last_health.get("ok"):
            print(f"Opencode is ready at http://{args.local_host}:{args.local_port}", flush=True)
            return True, last_health
        await asyncio.sleep(args.startup_poll_interval)
    return False, last_health


async def supervise(args: argparse.Namespace) -> None:
    restart_count = 0
    process: subprocess.Popen | None = None
    failures = 0
    try:
        while True:
            process = await start_bridge(args, restart_count)
            healthy, last_health = await wait_until_healthy(args, process, restart_count)
            if not healthy:
                stop_bridge(process)
                write_state(
                    args,
                    status="dead",
                    childPid=process.pid,
                    restartCount=restart_count,
                    lastHealth=last_health,
                    lastError=last_health.get("error"),
                )
                await wait_for_enter(
                    "Session did not start cleanly. Press Enter to reconnect Opencode, or Ctrl+C to stop."
                )
                restart_count += 1
                continue

            failures = 0
            while True:
                await asyncio.sleep(args.health_interval)
                if process.poll() is not None:
                    reason = f"bridge exited with code {process.returncode}"
                    write_state(
                        args,
                        status="dead",
                        childPid=process.pid,
                        restartCount=restart_count,
                        lastError=reason,
                    )
                    print(f"Opencode session died: {reason}", flush=True)
                    break
                health = await health_check(args)
                if health.get("ok"):
                    failures = 0
                    write_state(
                        args,
                        status="running",
                        childPid=process.pid,
                        restartCount=restart_count,
                        lastHealth=health,
                        lastError=None,
                    )
                    continue
                failures += 1
                write_state(
                    args,
                    status="degraded",
                    childPid=process.pid,
                    restartCount=restart_count,
                    consecutiveFailures=failures,
                    lastHealth=health,
                    lastError=health.get("error"),
                )
                print(f"Opencode health check failed ({failures}/{args.failure_threshold}): {health}", flush=True)
                if failures >= args.failure_threshold:
                    stop_bridge(process)
                    write_state(
                        args,
                        status="dead",
                        childPid=process.pid,
                        restartCount=restart_count,
                        consecutiveFailures=failures,
                        lastHealth=health,
                        lastError=health.get("error"),
                    )
                    break

            await wait_for_enter(
                "Session is down. Press Enter to reconnect Colab MCP and Opencode, or Ctrl+C to stop."
            )
            restart_count += 1
    finally:
        stop_bridge(process)
        write_state(args, status="stopped", childPid=None, restartCount=restart_count)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Watch the Colab Opencode localhost bridge and reconnect when Enter is pressed."
    )
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    parser.add_argument("--browser-command", default=os.environ.get("COLAB_MCP_BROWSER_COMMAND", "google-chrome-stable"))
    parser.add_argument("--browser-user-data-dir", default=os.environ.get("COLAB_MCP_BROWSER_USER_DATA_DIR", "/home/astra/.config/google-chrome"))
    parser.add_argument("--browser-profile", default=os.environ.get("COLAB_MCP_BROWSER_PROFILE", "Default"))
    parser.add_argument("--browser-headless", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--browser-copy-profile", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--browser-profile-copy-dir", default=os.environ.get("COLAB_MCP_BROWSER_PROFILE_COPY_DIR", "/tmp/colab-mcp-opencode-profile-copy"))
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
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    parser.add_argument("--bridge-log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--mcp-log-file", default="/tmp/colab-mcp-opencode-localhost.log")
    parser.add_argument("--health-interval", type=float, default=20.0)
    parser.add_argument("--health-timeout", type=float, default=10.0)
    parser.add_argument("--startup-timeout", type=float, default=300.0)
    parser.add_argument("--startup-poll-interval", type=float, default=5.0)
    parser.add_argument("--failure-threshold", type=int, default=2)
    parser.add_argument("--check-websocket", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    if not (1 <= args.local_port <= 65535):
        parser.error("--local-port must be between 1 and 65535")
    if args.health_interval <= 0:
        parser.error("--health-interval must be greater than 0")
    if args.health_timeout <= 0:
        parser.error("--health-timeout must be greater than 0")
    if args.startup_timeout <= 0:
        parser.error("--startup-timeout must be greater than 0")
    if args.failure_threshold <= 0:
        parser.error("--failure-threshold must be greater than 0")
    if args.drive_mount_timeout <= 0:
        parser.error("--drive-mount-timeout must be greater than 0")
    if args.drive_persistence and not args.drive_folder:
        parser.error("--drive-folder is required when drive persistence is enabled")
    if args.drive_persistence and not args.notebook_name.endswith(".ipynb"):
        parser.error("--notebook-name must end with .ipynb")
    return args


def main() -> None:
    try:
        asyncio.run(supervise(parse_args()))
    except KeyboardInterrupt:
        print("Stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
