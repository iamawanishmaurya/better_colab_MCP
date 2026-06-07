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
DEFAULT_CWD = "/content"
DEFAULT_DRIVE_FOLDER = "/content/drive/MyDrive/colab-terminal"
DEFAULT_NOTEBOOK_NAME = "colab-terminal.ipynb"
DEFAULT_TERMINAL_BACKEND = "ttyd"
DEFAULT_TERMINAL_COMMAND = "shell"
DEFAULT_GHOSTTOWN_SESSION_MODE = "direct"
DEFAULT_GHOSTTOWN_TMUX_SESSION = "drive-terminal"
GHOSTTOWN_PACKAGE = "@seflless/ghosttown"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


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


def setup_cell_code(
    *,
    port: int,
    cwd: str,
    install_timeout: int,
    drive_persistence: bool = True,
    drive_folder: str = DEFAULT_DRIVE_FOLDER,
    notebook_name: str = DEFAULT_NOTEBOOK_NAME,
    require_drive: bool = True,
    drive_mount_timeout: int = 180,
    terminal_backend: str = DEFAULT_TERMINAL_BACKEND,
    terminal_command: str = DEFAULT_TERMINAL_COMMAND,
    ghosttown_session_mode: str = DEFAULT_GHOSTTOWN_SESSION_MODE,
    ghosttown_tmux_session: str = DEFAULT_GHOSTTOWN_TMUX_SESSION,
) -> str:
    return f"""
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import signal
import socket
import subprocess
import time
import urllib.request

PORT = {port!r}
WORKDIR_REQUEST = {cwd!r}
INSTALL_TIMEOUT = {install_timeout!r}
DRIVE_PERSISTENCE = {drive_persistence!r}
DRIVE_FOLDER = {drive_folder!r}
NOTEBOOK_NAME = {notebook_name!r}
REQUIRE_DRIVE = {require_drive!r}
DRIVE_MOUNT_TIMEOUT = {drive_mount_timeout!r}
TERMINAL_BACKEND = {terminal_backend!r}
TERMINAL_COMMAND = {terminal_command!r}
GHOSTTOWN_SESSION_MODE = {ghosttown_session_mode!r}
GHOSTTOWN_TMUX_SESSION = {ghosttown_tmux_session!r}
GHOSTTOWN_PACKAGE = {GHOSTTOWN_PACKAGE!r}
if TERMINAL_BACKEND not in {{"ttyd", "ghosttown"}}:
    raise RuntimeError("Unsupported terminal backend: " + repr(TERMINAL_BACKEND))
if TERMINAL_COMMAND not in {{"opencode", "shell"}}:
    raise RuntimeError("Unsupported terminal command: " + repr(TERMINAL_COMMAND))
if GHOSTTOWN_SESSION_MODE not in {{"direct", "tmux"}}:
    raise RuntimeError("Unsupported Ghost Town session mode: " + repr(GHOSTTOWN_SESSION_MODE))
if GHOSTTOWN_SESSION_MODE == "tmux":
    if not GHOSTTOWN_TMUX_SESSION:
        raise RuntimeError("Ghost Town tmux mode requires a tmux session name")
    if any(char in GHOSTTOWN_TMUX_SESSION for char in "\\n\\r:"):
        raise RuntimeError("Ghost Town tmux session name cannot contain newline or ':'")

LOG_PATH = "/content/colab-terminal-" + TERMINAL_BACKEND + ".log"
PID_PATH = "/content/colab-terminal-" + TERMINAL_BACKEND + ".pid"
SESSION_STATE_PATH = "/content/colab-terminal-session-state.json"
DRIVE_SUMMARY = {{}}
PERSISTENCE_LINKS = []
RECOVERY_FILES = []
WORKDIR = WORKDIR_REQUEST


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


class DriveMountTimeout(RuntimeError):
    pass


def mount_drive():
    if not DRIVE_PERSISTENCE:
        return {{"enabled": False, "mounted": False, "folder": None}}
    if Path("/content/drive/MyDrive").exists():
        return {{"enabled": True, "mounted": True, "folder": DRIVE_FOLDER, "alreadyMounted": True}}
    try:
        from google.colab import drive
    except Exception as exc:
        if REQUIRE_DRIVE:
            raise RuntimeError("Google Drive persistence requested but google.colab.drive is unavailable") from exc
        return {{"enabled": True, "mounted": False, "folder": DRIVE_FOLDER, "error": repr(exc)}}

    def on_timeout(_signum, _frame):
        raise DriveMountTimeout("Google Drive mount timed out after %s seconds" % DRIVE_MOUNT_TIMEOUT)

    old_handler = signal.signal(signal.SIGALRM, on_timeout)
    signal.alarm(int(DRIVE_MOUNT_TIMEOUT))
    try:
        drive.mount("/content/drive", force_remount=False)
    except Exception as exc:
        if REQUIRE_DRIVE:
            raise RuntimeError("Google Drive mount failed. Complete the Colab Drive authorization prompt and rerun setup.") from exc
        return {{"enabled": True, "mounted": False, "folder": DRIVE_FOLDER, "error": repr(exc)}}
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    mounted = Path("/content/drive/MyDrive").exists()
    if REQUIRE_DRIVE and not mounted:
        raise RuntimeError("Google Drive did not mount at /content/drive/MyDrive")
    return {{"enabled": True, "mounted": mounted, "folder": DRIVE_FOLDER}}


def merge_existing_directory(source, target):
    source_path = Path(source).expanduser()
    target_path = Path(target)
    target_path.mkdir(parents=True, exist_ok=True)
    if not source_path.exists() or source_path.is_symlink():
        return
    if source_path.is_dir():
        shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        shutil.rmtree(source_path)
    else:
        shutil.copy2(source_path, target_path / source_path.name)
        source_path.unlink()


def ensure_persistent_dir(runtime_path, drive_path):
    runtime = Path(runtime_path).expanduser()
    drive = Path(drive_path)
    drive.mkdir(parents=True, exist_ok=True)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    if runtime.is_symlink():
        try:
            if runtime.resolve() == drive.resolve():
                return {{"runtime": str(runtime), "drive": str(drive), "linked": True, "alreadyLinked": True}}
        except FileNotFoundError:
            pass
        runtime.unlink()
    elif runtime.exists():
        merge_existing_directory(runtime, drive)
    runtime.symlink_to(drive, target_is_directory=True)
    return {{"runtime": str(runtime), "drive": str(drive), "linked": True}}


def ensure_temporary_cache_dir(runtime_path, cache_path):
    runtime = Path(runtime_path).expanduser()
    cache = Path(cache_path)
    cache.mkdir(parents=True, exist_ok=True)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    if runtime.is_symlink():
        try:
            if runtime.resolve() == cache.resolve():
                return {{"runtime": str(runtime), "target": str(cache), "linked": True, "temporary": True, "alreadyLinked": True}}
        except FileNotFoundError:
            pass
        runtime.unlink()
    elif runtime.exists():
        merge_existing_directory(runtime, cache)
    runtime.symlink_to(cache, target_is_directory=True)
    return {{"runtime": str(runtime), "target": str(cache), "linked": True, "temporary": True}}


def write_recovery_files(drive_root, workdir):
    drive_path = Path(drive_root)
    drive_path.mkdir(parents=True, exist_ok=True)
    notebook_path = drive_path / NOTEBOOK_NAME
    recovery_dir = drive_path / "recovery"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    script_path = recovery_dir / "reconnect.sh"
    state_readme_path = drive_path / "README.md"
    script = (
        "#!/usr/bin/env bash\\n"
        "set -euo pipefail\\n"
        "export PATH=\\"$HOME/.opencode/bin:$PATH\\"\\n"
        "cd %s\\n"
        "%s\\n"
    ) % (shlex.quote(str(workdir)), terminal_exec_line())
    script_path.write_text(script, encoding="utf-8")
    os.chmod(script_path, 0o755)
    if not notebook_path.exists():
        notebook = {{
            "nbformat": 4,
            "nbformat_minor": 5,
            "metadata": {{
                "colab": {{"name": NOTEBOOK_NAME}},
                "kernelspec": {{"name": "python3", "display_name": "Python 3"}},
                "language_info": {{"name": "python"}},
            }},
            "cells": [
                {{
                    "cell_type": "markdown",
                    "metadata": {{}},
                    "source": [
                        "# Colab Terminal Recovery\\n",
                        "\\n",
                        "This notebook was generated by better_colab_MCP. Runtime project files and app session data are stored in Google Drive.\\n",
                    ],
                }},
                {{
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {{}},
                    "outputs": [],
                    "source": [
                        "from google.colab import drive\\n",
                        "drive.mount('/content/drive')\\n",
                        "import os\\n",
                        "os.chdir(%r)\\n" % str(workdir),
                        "!bash %s\\n" % shlex.quote(str(script_path)),
                    ],
                }},
            ],
        }}
        notebook_path.write_text(json.dumps(notebook, indent=1) + "\\n", encoding="utf-8")
    state_readme_path.write_text(
        "Colab terminal persistence\\n\\n"
        "Workspace folder: %s\\n"
        "Persistent config: %s\\n"
        "Persistent app data: %s\\n"
        "Temporary cache: %s\\n"
        "Recovery notebook: %s\\n"
        "Recovery script: %s\\n"
        "Default terminal command: %s\\n"
        % (
            str(workdir),
            str(drive_path / "home" / ".config"),
            str(drive_path / "home" / ".local" / "share"),
            "/content/colab-terminal-cache",
            str(notebook_path),
            str(script_path),
            TERMINAL_COMMAND,
        ),
        encoding="utf-8",
    )
    return [str(notebook_path), str(script_path), str(state_readme_path)]


def configure_persistence():
    global DRIVE_SUMMARY, PERSISTENCE_LINKS, RECOVERY_FILES, WORKDIR
    DRIVE_SUMMARY = mount_drive()
    if not DRIVE_PERSISTENCE or not DRIVE_SUMMARY.get("mounted"):
        WORKDIR = WORKDIR_REQUEST
        Path(WORKDIR).mkdir(parents=True, exist_ok=True)
        PERSISTENCE_LINKS = [
            ensure_temporary_cache_dir("~/.cache", "/content/colab-terminal-cache"),
        ]
        return

    drive_root = Path(DRIVE_FOLDER)
    drive_root.mkdir(parents=True, exist_ok=True)
    if WORKDIR_REQUEST in ("", "/content", "/content/"):
        WORKDIR = str(drive_root / "projects" / "project")
    else:
        WORKDIR = WORKDIR_REQUEST
    Path(WORKDIR).mkdir(parents=True, exist_ok=True)

    PERSISTENCE_LINKS = [
        ensure_persistent_dir("~/.config", drive_root / "home" / ".config"),
        ensure_persistent_dir("~/.local/share", drive_root / "home" / ".local" / "share"),
        ensure_temporary_cache_dir("~/.cache", "/content/colab-terminal-cache"),
    ]
    RECOVERY_FILES = write_recovery_files(drive_root, Path(WORKDIR))
    emit("Drive persistence root: " + str(drive_root))
    emit("Terminal working directory: " + str(WORKDIR))


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


def install_node_runtime():
    missing = [name for name in ("node", "npm") if not shutil.which(name)]
    if GHOSTTOWN_SESSION_MODE == "tmux" and not shutil.which("tmux"):
        missing.append("tmux")
    if missing:
        packages = "nodejs npm"
        if GHOSTTOWN_SESSION_MODE == "tmux":
            packages += " tmux"
        run(
            "apt-get update -y && DEBIAN_FRONTEND=noninteractive apt-get install -y " + packages,
            timeout=600,
        )
    version_check = "node --version && npm --version"
    if GHOSTTOWN_SESSION_MODE == "tmux":
        version_check += " && tmux -V"
    run(version_check, timeout=120)


def install_ghosttown():
    install_node_runtime()
    if shutil.which("ghosttown"):
        emit("ghosttown already installed: " + shutil.which("ghosttown"))
        return
    run(
        "npm install -g " + shlex.quote(GHOSTTOWN_PACKAGE),
        timeout=INSTALL_TIMEOUT + 120,
    )
    if not shutil.which("ghosttown"):
        raise RuntimeError("ghosttown was not found on PATH after npm install")


def write_ghosttown_shell():
    shell_path = Path("/content/colab-terminal-ghosttown-shell.sh")
    if GHOSTTOWN_SESSION_MODE == "tmux":
        launch = terminal_launch_command()
        script = (
            "#!/usr/bin/env bash\\n"
            "set -euo pipefail\\n"
            "export PATH=\\"$HOME/.opencode/bin:$PATH\\"\\n"
            "cd %s\\n"
            "if ! tmux has-session -t %s 2>/dev/null; then\\n"
            "  tmux new-session -d -s %s -c %s /bin/bash -lc %s\\n"
            "fi\\n"
            "exec tmux attach-session -t %s\\n"
        ) % (
            shlex.quote(WORKDIR),
            shlex.quote(GHOSTTOWN_TMUX_SESSION),
            shlex.quote(GHOSTTOWN_TMUX_SESSION),
            shlex.quote(WORKDIR),
            shlex.quote(launch),
            shlex.quote(GHOSTTOWN_TMUX_SESSION),
        )
    else:
        exec_line = terminal_exec_line()
        script = (
            "#!/usr/bin/env bash\\n"
            "set -euo pipefail\\n"
            "export PATH=\\"$HOME/.opencode/bin:$PATH\\"\\n"
            "cd %s\\n"
            "%s\\n"
        ) % (shlex.quote(WORKDIR), exec_line)
    shell_path.write_text(script, encoding="utf-8")
    os.chmod(shell_path, 0o755)
    return str(shell_path)


def terminal_exec_line():
    if TERMINAL_COMMAND == "shell":
        return "exec /bin/bash -l"
    return "exec opencode"


def opencode_launch_command():
    return (
        "export PATH=$HOME/.opencode/bin:$PATH; "
        + "cd "
        + shlex.quote(WORKDIR)
        + "; "
        + "exec opencode"
    )


def terminal_launch_command():
    if TERMINAL_COMMAND == "shell":
        return (
            "export PATH=$HOME/.opencode/bin:$PATH; "
            + "cd "
            + shlex.quote(WORKDIR)
            + "; "
            + terminal_exec_line()
        )
    return opencode_launch_command()


def ensure_ghosttown_tmux_session():
    if GHOSTTOWN_SESSION_MODE != "tmux":
        return False
    launch = terminal_launch_command()
    command = (
        "tmux has-session -t "
        + shlex.quote(GHOSTTOWN_TMUX_SESSION)
        + " 2>/dev/null || tmux new-session -d -s "
        + shlex.quote(GHOSTTOWN_TMUX_SESSION)
        + " -c "
        + shlex.quote(WORKDIR)
        + " /bin/bash -lc "
        + shlex.quote(launch)
    )
    run(command, timeout=30)
    return True


def port_open(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", int(port))) == 0


def start_ttyd():
    Path(WORKDIR).mkdir(parents=True, exist_ok=True)
    run(f"fuser -k {{PORT}}/tcp >/dev/null 2>&1 || true", timeout=20, check=False)
    launch = terminal_launch_command()
    title = "Colab-Terminal" if TERMINAL_COMMAND == "shell" else "OpenCode-Colab"
    command = (
        "nohup ttyd -W -p "
        + str(PORT)
        + " -t titleFixed="
        + shlex.quote(title)
        + " "
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


def start_ghosttown():
    Path(WORKDIR).mkdir(parents=True, exist_ok=True)
    run(f"fuser -k {{PORT}}/tcp >/dev/null 2>&1 || true", timeout=20, check=False)
    ensure_ghosttown_tmux_session()
    shell_path = write_ghosttown_shell()
    command = (
        "SHELL="
        + shlex.quote(shell_path)
        + " nohup ghosttown -p "
        + str(PORT)
        + " --http --no-auth > "
        + shlex.quote(LOG_PATH)
        + " 2>&1 & echo $! > "
        + shlex.quote(PID_PATH)
    )
    run(command, timeout=30)
    deadline = time.time() + 45
    while time.time() < deadline:
        if port_open(PORT):
            return
        time.sleep(1)
    tail = Path(LOG_PATH).read_text(errors="replace")[-4000:] if Path(LOG_PATH).exists() else ""
    raise RuntimeError("ghosttown did not open the requested port. Log tail:\\n" + tail)


configure_persistence()
if TERMINAL_COMMAND == "opencode":
    install_opencode()
    run("opencode --version", timeout=60)
if TERMINAL_BACKEND == "ghosttown":
    install_ghosttown()
    run("ghosttown --version", timeout=60)
    start_ghosttown()
else:
    install_ttyd()
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
    "terminalBackend": TERMINAL_BACKEND,
    "terminalCommand": TERMINAL_COMMAND,
    "terminalLaunchCommand": terminal_launch_command(),
    "ghosttownSessionMode": GHOSTTOWN_SESSION_MODE if TERMINAL_BACKEND == "ghosttown" else None,
    "ghosttownTmuxSession": GHOSTTOWN_TMUX_SESSION if TERMINAL_BACKEND == "ghosttown" and GHOSTTOWN_SESSION_MODE == "tmux" else None,
    "ghosttownTmuxAttachCommand": ("tmux attach -t " + GHOSTTOWN_TMUX_SESSION) if TERMINAL_BACKEND == "ghosttown" and GHOSTTOWN_SESSION_MODE == "tmux" else None,
    "drive": DRIVE_SUMMARY,
    "persistenceLinks": PERSISTENCE_LINKS,
    "recoveryFiles": RECOVERY_FILES,
    "sessionStatePath": SESSION_STATE_PATH,
    "logPath": LOG_PATH,
    "pidPath": PID_PATH,
    "opencode": shutil.which("opencode"),
    "ghosttown": shutil.which("ghosttown"),
    "ghosttownShellPath": "/content/colab-terminal-ghosttown-shell.sh" if TERMINAL_BACKEND == "ghosttown" else None,
    "ghosttownNewSessionPath": "/new" if TERMINAL_BACKEND == "ghosttown" else None,
    "ttyd": shutil.which("ttyd"),
    "portOpen": port_open(PORT),
    "proxyUrl": proxy_url,
    "proxyUrlError": proxy_url_error,
}}
Path(SESSION_STATE_PATH).write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
if DRIVE_PERSISTENCE and DRIVE_SUMMARY.get("mounted"):
    drive_state = Path(DRIVE_FOLDER) / "sessions" / "terminal-state.json"
    drive_state.parent.mkdir(parents=True, exist_ok=True)
    drive_state.write_text(json.dumps(result, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
payload = json.dumps(result, sort_keys=True)
emit("COLAB_TERMINAL_RESULT " + payload)
emit("COLAB_OPENCODE_RESULT " + payload)
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
            drive_persistence=args.drive_persistence,
            drive_folder=args.drive_folder,
            notebook_name=args.notebook_name,
            require_drive=args.require_drive,
            drive_mount_timeout=args.drive_mount_timeout,
            terminal_backend=args.terminal_backend,
            terminal_command=args.terminal_command,
            ghosttown_session_mode=args.ghosttown_session_mode,
            ghosttown_tmux_session=args.ghosttown_tmux_session,
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
        print(f"Opencode {args.terminal_backend} web terminal is running in Colab.", flush=True)
        print(f"Open the Colab output iframe/window on port {args.port}.", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Opencode in Colab and expose it through a web terminal."
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
    parser.add_argument("--cwd", default=os.environ.get("COLAB_OPENCODE_CWD", DEFAULT_CWD))
    parser.add_argument(
        "--terminal-backend",
        choices=("ttyd", "ghosttown"),
        default=os.environ.get("COLAB_OPENCODE_TERMINAL_BACKEND", DEFAULT_TERMINAL_BACKEND),
        help="Terminal web backend to start in Colab.",
    )
    parser.add_argument(
        "--terminal-command",
        choices=("opencode", "shell"),
        default=os.environ.get("COLAB_OPENCODE_TERMINAL_COMMAND", DEFAULT_TERMINAL_COMMAND),
        help="Command opened by the web terminal. Use 'shell' for a normal Drive-rooted Bash terminal.",
    )
    parser.add_argument(
        "--ghosttown-session-mode",
        choices=("direct", "tmux"),
        default=os.environ.get("COLAB_OPENCODE_GHOSTTOWN_SESSION_MODE", DEFAULT_GHOSTTOWN_SESSION_MODE),
        help="For Ghost Town, launch OpenCode directly or through a reusable tmux session.",
    )
    parser.add_argument(
        "--ghosttown-tmux-session",
        default=os.environ.get("COLAB_OPENCODE_GHOSTTOWN_TMUX_SESSION", DEFAULT_GHOSTTOWN_TMUX_SESSION),
        help="tmux session name used when --ghosttown-session-mode=tmux.",
    )
    parser.add_argument(
        "--drive-persistence",
        action=argparse.BooleanOptionalAction,
        default=env_bool("COLAB_OPENCODE_DRIVE_PERSISTENCE", True),
        help="Mount Google Drive and persist Opencode project/session data under --drive-folder.",
    )
    parser.add_argument("--drive-folder", default=os.environ.get("COLAB_OPENCODE_DRIVE_FOLDER", DEFAULT_DRIVE_FOLDER))
    parser.add_argument("--notebook-name", default=os.environ.get("COLAB_OPENCODE_NOTEBOOK_NAME", DEFAULT_NOTEBOOK_NAME))
    parser.add_argument(
        "--require-drive",
        action=argparse.BooleanOptionalAction,
        default=env_bool("COLAB_OPENCODE_REQUIRE_DRIVE", True),
        help="Fail setup if Google Drive cannot be mounted when drive persistence is enabled.",
    )
    parser.add_argument(
        "--drive-mount-timeout",
        type=int,
        default=int(os.environ.get("COLAB_OPENCODE_DRIVE_MOUNT_TIMEOUT", "180")),
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
    if args.drive_mount_timeout <= 0:
        parser.error("--drive-mount-timeout must be greater than 0")
    if args.drive_persistence and not args.drive_folder:
        parser.error("--drive-folder is required when drive persistence is enabled")
    if args.drive_persistence and not args.notebook_name.endswith(".ipynb"):
        parser.error("--notebook-name must end with .ipynb")
    if args.ghosttown_session_mode == "tmux":
        if not args.ghosttown_tmux_session:
            parser.error("--ghosttown-tmux-session is required in tmux mode")
        if any(char in args.ghosttown_tmux_session for char in "\n\r:"):
            parser.error("--ghosttown-tmux-session cannot contain newline or ':'")
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
