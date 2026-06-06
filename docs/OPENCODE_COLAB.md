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
