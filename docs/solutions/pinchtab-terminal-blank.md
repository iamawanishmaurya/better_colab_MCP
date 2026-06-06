# PinchTab Terminal View Is Blank

- Problem: [docs/problems/2026-06-06-pinchtab-terminal-blank.md](../problems/2026-06-06-pinchtab-terminal-blank.md)

## What Failed

The local Opencode bridge served ttyd HTML and loaded `window.term`, but the PinchTab screenshot stayed as an empty dark terminal viewport. The bridge log showed:

```text
127.0.0.1: Client protocols ['tty'] don’t overlap server-known ones ()
```

The local aiohttp WebSocket endpoint accepted the browser WebSocket without advertising ttyd's `tty` subprotocol, so the browser-side terminal stream did not negotiate the same protocol path as ttyd expects.

## What Worked

The localhost bridge now:

- Parses `Sec-WebSocket-Protocol` from the browser request.
- Advertises those protocols on `web.WebSocketResponse`.
- Passes the same protocols to `ClientSession.ws_connect` upstream.
- Excludes generated WebSocket handshake headers before forwarding custom headers upstream.

The supervisor health check also validates the browser-relevant `tty` WebSocket protocol.

## Why It Worked

ttyd's browser client opens `/ws` with the `tty` WebSocket subprotocol. Preserving that protocol on both sides of the reverse proxy makes the local browser, local aiohttp proxy, Colab runtime proxy, and ttyd agree on the stream format. After restarting the supervisor with the patched proxy, PinchTab rendered the Opencode TUI instead of a blank terminal.

## Commands Run

```bash
uv run pytest -q tests/opencode_localhost_proxy_test.py
uv run ruff check .
uv run python -m compileall -f src scripts
uv run pytest -q
tmux kill-session -t colab-opencode-supervisor || true
tmux new-session -d -s colab-opencode-supervisor 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_supervisor.py --repo /home/astra/codex/Google-Colab/better_colab_MCP --state-file /tmp/colab-mcp-opencode-session-state.json --bridge-log-file /tmp/colab-mcp-opencode-supervised-bridge.log --mcp-log-file /tmp/colab-mcp-opencode-localhost.log'
for i in {1..60}; do state_value=$(python - <<'PY'
import json
from pathlib import Path
p=Path('/tmp/colab-mcp-opencode-session-state.json')
print(json.loads(p.read_text()).get('status') if p.exists() else 'missing')
PY
); echo "$(date -Iseconds) state=$state_value"; [ "$state_value" = running ] && break; sleep 5; done
export PINCHTAB_SESSION=$(pinchtab session create --agent-id colab-opencode-pinchtest-fixed)
pinchtab nav http://127.0.0.1:8765 --snap
PINCHTAB_SESSION=$PINCHTAB_SESSION pinchtab eval --json '({title: document.title, url: location.href, hasTerm: Boolean(window.term), rows: window.term && window.term.rows, cols: window.term && window.term.cols, terminalContainer: Boolean(document.querySelector("#terminal-container")), cursorCanvas: Boolean(document.querySelector("canvas.xterm-cursor-layer")), bodyTextLength: document.body.innerText.length})'
PINCHTAB_SESSION=$PINCHTAB_SESSION pinchtab screenshot --format png -o /tmp/colab-opencode-pinchtab-fixed-waited.png
```

Validation evidence:

- Focused proxy regression test: `2 passed`.
- Full test suite: `66 passed`.
- Supervisor state: `status=running`, `httpOk=true`, `websocketOk=true`.
- PinchTab title: `OpenCode-Colab`.
- PinchTab terminal dimensions: `132x58`.
- Screenshot: `/tmp/colab-opencode-pinchtab-fixed-waited.png` showed the Opencode TUI at `/content`, version `1.16.2`.
