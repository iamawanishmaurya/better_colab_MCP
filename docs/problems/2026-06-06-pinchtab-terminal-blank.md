# PinchTab Terminal View Is Blank

- Timestamp: 2026-06-06T16:35:55+05:30
- Environment: Arch Linux workstation, PinchTab `pinchtab` from `/home/astra/.npm-global/bin/pinchtab`, headed PinchTab default profile `prof_1ff0e382` (`niet-student-vps`), local Opencode bridge at `http://127.0.0.1:8765`, supervisor state file `/tmp/colab-mcp-opencode-session-state.json`.

## Exact Error

PinchTab successfully opened `http://127.0.0.1:8765/` and the in-tab evaluation showed `window.term` loaded, but the saved screenshot `/tmp/colab-opencode-pinchtab.png` was a dark empty terminal viewport with no Opencode UI text.

The local bridge log also showed:

```text
127.0.0.1: Client protocols ['tty'] don’t overlap server-known ones ()
127.0.0.1: Client protocols ['tty'] don’t overlap server-known ones ()
127.0.0.1: Client protocols ['tty'] don’t overlap server-known ones ()
```

## Reproduction Steps

1. Start the supervised Opencode bridge:
   ```bash
   tmux new-session -d -s colab-opencode-supervisor 'uv run python scripts/colab_opencode_supervisor.py --repo /home/astra/codex/Google-Colab/better_colab_MCP'
   ```
2. Open the local bridge in PinchTab:
   ```bash
   export PINCHTAB_SESSION=$(pinchtab session create --agent-id colab-opencode-pinchtest)
   pinchtab nav http://127.0.0.1:8765 --snap
   ```
3. Verify browser-side terminal state:
   ```bash
   PINCHTAB_SESSION=$PINCHTAB_SESSION pinchtab eval --json '({title: document.title, url: location.href, hasTerm: Boolean(window.term), rows: window.term && window.term.rows, cols: window.term && window.term.cols, terminalContainer: Boolean(document.querySelector("#terminal-container")), textCanvas: Boolean(document.querySelector("canvas.xterm-text-layer")), cursorCanvas: Boolean(document.querySelector("canvas.xterm-cursor-layer"))})'
   ```
4. Save a screenshot:
   ```bash
   PINCHTAB_SESSION=$PINCHTAB_SESSION pinchtab screenshot --format png -o /tmp/colab-opencode-pinchtab.png
   ```

## First Hypothesis

The local reverse proxy does not preserve ttyd's `tty` WebSocket subprotocol. The browser requests `tty`, but the aiohttp local WebSocket endpoint advertises no known subprotocols, which may prevent ttyd's terminal stream from negotiating correctly and leaves the xterm canvas empty.
