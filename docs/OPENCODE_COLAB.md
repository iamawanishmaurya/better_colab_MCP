# Opencode In Colab

This workflow installs Opencode inside the Colab runtime and exposes it through
`ttyd`, a browser-based PTY terminal. It can also expose Opencode through
Ghost Town, a Ghostty-powered browser terminal. Use this for full-screen interactive
programs; the cell terminal bridge is only a command runner and is not a real
PTY.

Start setup from this repository:

```shell
uv run python scripts/colab_opencode_web_terminal.py
```

The script:

- Starts a client-managed `colab-mcp` server.
- Opens the Colab scratch URL in Chrome profile `Default`.
- Mounts Google Drive by default. If Colab shows a Drive authorization prompt,
  complete that prompt in the browser before rerunning setup.
- Creates `/content/drive/MyDrive/opencode`.
- Uses `/content/drive/MyDrive/opencode/project` as the default Opencode
  working directory when `--cwd` is left as `/content`.
- Writes a recovery notebook named `opencode.ipynb`, a recovery shell script,
  and `opencode-session-state.json` under the Drive folder.
- Symlinks OpenCode state/config/cache paths into the Drive folder, including
  `~/.local/share/opencode`, so chats and project session data survive runtime
  loss.
- Installs Opencode with the official `https://opencode.ai/install` script using
  bounded curl timeouts.
- Installs `ttyd` through `apt`, with a GitHub release binary fallback.
- Starts `ttyd` on Colab port `7681`.
- Opens a Colab output window/iframe for the web terminal.

Useful flags:

```shell
uv run python scripts/colab_opencode_web_terminal.py --port 7682 --cwd /content/project
uv run python scripts/colab_opencode_web_terminal.py --setup-timeout 1200 --print-url
uv run python scripts/colab_opencode_web_terminal.py --no-auto-click-connect
uv run python scripts/colab_opencode_web_terminal.py --no-drive-persistence --cwd /content
uv run python scripts/colab_opencode_web_terminal.py --no-require-drive
uv run python scripts/colab_opencode_web_terminal.py --terminal-backend ghosttown
uv run python scripts/colab_opencode_web_terminal.py --terminal-backend ghosttown --ghosttown-session-mode tmux
```

Use `--no-require-drive` only for smoke tests or temporary sessions where Drive
authorization is unavailable. It still attempts to mount Drive, but it falls
back to the requested runtime directory if Colab refuses or times out.

## Ghost Town Backend

Ghostty itself is a native desktop terminal, not a Colab web server. For a
browser-based Ghostty-powered terminal, use Ghost Town:

```shell
uv run python scripts/colab_opencode_web_terminal.py \
  --terminal-backend ghosttown \
  --drive-folder /content/drive/MyDrive/opencode \
  --notebook-name opencode.ipynb
```

The setup cell installs `@seflless/ghosttown`, writes
`/content/opencode-ghosttown-shell.sh`, and starts the Ghost Town web server on
the selected Colab port. Open `/new` on the Ghost Town URL to create a
web-managed terminal session that launches Opencode in the persistent project
directory.

To make the Ghost Town browser terminal attach directly to a tmux session in
Colab, use tmux mode:

```shell
uv run python scripts/colab_opencode_web_terminal.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --ghosttown-tmux-session opencode
```

In tmux mode, setup installs `tmux`, creates or reuses the named `opencode`
session, starts OpenCode inside that session, and makes every Ghost Town `/new`
terminal attach to it. This is still not SSH; it is Ghost Town's browser PTY
connected to Colab's kernel port proxy.

For localhost access through the local reverse proxy:

```shell
uv run python scripts/colab_opencode_localhost.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --local-port 8765
```

When the bridge prints `Ghost Town new Opencode session URL`, open that `/new`
URL to create a terminal session that starts Opencode.

For supervised reconnects:

```shell
uv run python scripts/colab_opencode_supervisor.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --local-port 8765
```

The supervisor keeps the same Enter-to-reconnect loop. For Ghost Town, health
checks verify HTTP availability; ttyd-specific `/ws` protocol probing is only
used for the `ttyd` backend.

## Localhost Without SSH

Use `scripts/colab_opencode_localhost.py` when you want the Colab-hosted
Opencode PTY to be reachable from this laptop as `localhost`.

```shell
uv run python scripts/colab_opencode_localhost.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765
```

The script:

- Connects Colab MCP through copied-profile headless CDP.
- Connects the Colab runtime.
- Mounts Drive by default and prepares the persistent Opencode folder.
- Installs/starts Opencode and the selected web terminal backend on the remote
  Colab port.
- Reads the Colab kernel proxy URL.
- Starts a local HTTP/WebSocket reverse proxy at `http://127.0.0.1:8765`.
- Runs a localhost smoke request before staying attached.

For non-interactive validation:

```shell
uv run python scripts/colab_opencode_localhost.py --exit-after-smoke
```

This is not SSH. It is a local reverse proxy to Colab's kernel port proxy. If
the Colab runtime stops, the local URL will stop working until the script is run
again.

## Enter-To-Reconnect Supervisor

Use `scripts/colab_opencode_supervisor.py` when you want the bridge to record
session state and wait for Enter before reconnecting after the local or Colab
session dies.

```shell
uv run python scripts/colab_opencode_supervisor.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765
```

The supervisor writes state to:

```text
/tmp/colab-mcp-opencode-session-state.json
```

When health checks fail or the bridge exits, it marks the session `dead` and
prints:

```text
Session is down. Press Enter to reconnect Colab MCP and Opencode, or Ctrl+C to stop.
```

Press Enter in the supervisor terminal to restart the MCP connection, reconnect
the Colab runtime, restart ttyd/Opencode, and restore localhost access.

To keep the supervisor attachable across shell interruptions, run it in tmux:

```shell
tmux new-session -s colab-opencode-supervisor
uv run python scripts/colab_opencode_supervisor.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765
```

Attach later and press Enter if the supervisor reports a dead session:

```shell
tmux attach -t colab-opencode-supervisor
```

Runtime paths:

- Opencode binary: `/root/.opencode/bin/opencode`
- Persistent Drive root: `/content/drive/MyDrive/opencode`
- Persistent project folder: `/content/drive/MyDrive/opencode/project`
- Recovery notebook: `/content/drive/MyDrive/opencode/opencode.ipynb`
- Runtime state: `/content/opencode-session-state.json`
- Drive state copy: `/content/drive/MyDrive/opencode/opencode-session-state.json`
- Backend log: `/content/opencode-ttyd.log` or `/content/opencode-ghosttown.log`
- Backend PID file: `/content/opencode-ttyd.pid` or `/content/opencode-ghosttown.pid`
- Ghost Town OpenCode shell: `/content/opencode-ghosttown-shell.sh`
- Ghost Town tmux attach command: `tmux attach -t opencode`

Requirements:

- The Colab browser page must connect to MCP.
- When Chrome is already running without CDP, the script tries to accept Colab's
  local MCP Connect dialog through visible-browser Hyprland/ydotool automation.
  It opens a fresh Chrome window with the scratch URL, then retries `enter`,
  `tab-enter`, and `tab-tab-enter` unless disabled.
- The Colab notebook execution slot must be free. If a prior cell is stuck,
  interrupt it in the Colab UI with `Ctrl+M`, then `I`, before running setup.
- Opencode still needs provider API keys or provider login/configuration before
  it can complete model-backed tasks.
