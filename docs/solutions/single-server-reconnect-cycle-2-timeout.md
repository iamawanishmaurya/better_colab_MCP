# Solution: Single-Server Reconnect Cycle 2 Timeout

Links back to: `docs/problems/2026-06-06-single-server-reconnect-cycle-2-timeout.md`

## What Failed

Visible key automation could connect cycle 1, and closing the scratch tab made the server report `connected=false`, but cycle 2 did not reconnect. The browser-side Colab MCP service kept stale token/port state that keyboard automation could not reliably reset.

## What Worked

Copied-profile headless CDP mode connected three fresh MCP server cycles without manual clicks:

- cycle 1: `connected=True`, `65.2s`, marker code cell ran
- cycle 2: `connected=True`, `8.2s`
- cycle 3: `connected=True`, `9.1s`

## Why It Worked

CDP can directly navigate the Colab page, set `sessionStorage.mcp_proxy_token` and `sessionStorage.mcp_proxy_port`, disconnect stale service state when token/port mismatch, and call `localColabMcpService.connect()`. Visible keyboard automation can only press dialog buttons and cannot reliably repair stale browser-side service state.

## Commands Run

```bash
uv run ruff check .
uv run python -m compileall -f src scripts
uv run pytest tests/session_test.py -q

COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_HEADLESS=1 \
COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_BROWSER_COPY_PROFILE=1 \
COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-profile-copy-live \
COLAB_MCP_EDGE_CDP_PORT=9457 \
COLAB_MCP_CONNECTION_TIMEOUT=240 \
uv run python -
```
