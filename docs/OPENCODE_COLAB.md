# Opencode In Colab

This workflow installs Opencode inside the Colab runtime and exposes it through
`ttyd`, a browser-based PTY terminal. Use this for full-screen interactive
programs; the cell terminal bridge is only a command runner and is not a real
PTY.

Start setup from this repository:

```shell
uv run python scripts/colab_opencode_web_terminal.py
```

The script:

- Starts a client-managed `colab-mcp` server.
- Opens the Colab scratch URL in Chrome profile `Default`.
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
```

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
- Installs/starts Opencode and `ttyd` on the remote Colab port.
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
- TTYD log: `/content/opencode-ttyd.log`
- TTYD PID file: `/content/opencode-ttyd.pid`

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
