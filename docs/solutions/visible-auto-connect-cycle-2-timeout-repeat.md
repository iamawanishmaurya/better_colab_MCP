# Solution: Visible Auto-Connect Cycle 2 Timeout Repeat

Links back to: `docs/problems/2026-06-06-visible-auto-connect-cycle-2-timeout-repeat.md`

## What Failed

After the stale-tab visible fallback change, cycle 2 still failed after four key-driven attempts. This repeated the same failure class: visible keyboard automation could not reliably reset Colab's browser-side MCP service state.

## What Worked

Copied-profile headless CDP mode replaced the keyboard retry strategy for reliable reconnects. It passed three MCP server cycles against the copied `Default` profile with no manual clicking.

## Why It Worked

Repeated key retries were acting on focus/dialog symptoms. CDP acts on the page state directly, updates token/port session storage, disconnects mismatches, and calls the frontend MCP service.

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
