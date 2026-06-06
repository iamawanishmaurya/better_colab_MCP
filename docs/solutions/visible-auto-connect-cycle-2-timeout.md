# Solution: Visible Auto-Connect Cycle 2 Timeout

Links back to: `docs/problems/2026-06-06-visible-auto-connect-cycle-2-timeout.md`

## What Failed

The first visible auto-connect cycle succeeded, but cycle 2 timed out after `enter`, `tab-enter`, and `tab-tab-enter` attempts. Keyboard automation could not guarantee that the intended Colab tab/dialog had focus or that stale browser-side MCP state was reset.

## What Worked

Direct CDP connection with copied-profile headless auth worked. The server now uses CDP to set the MCP token/port and invoke the Colab MCP service directly. The three-cycle copied-profile test connected all cycles and ran a code cell in cycle 1.

## Why It Worked

The failing path depended on visible focus and dialog state. The working path controls the actual Colab page over CDP and calls `localColabMcpService.connect()` programmatically, so it does not need the user to click Connect or rely on `ydotool`.

## Commands Run

```bash
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
