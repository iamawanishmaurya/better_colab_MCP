# Solution: Visible Auto-Connect No Colab Window

Links back to: `docs/problems/2026-06-06-visible-auto-connect-no-colab-window.md`

## What Failed

Visible automation could not find a Colab-titled Chrome window during reconnect testing. Even the any-Chrome fallback remained sensitive to focus and tab targeting.

## What Worked

Headless copied-profile CDP mode does not require a visible Colab window. It launches a controlled headless Chrome from a copied profile, opens the Colab scratch URL over CDP, and connects the frontend MCP service directly.

## Why It Worked

The failure depended on compositor/window state. CDP targets the browser page by debugger endpoint and Colab URL, so it works without a focused window title.

## Commands Run

```bash
ss -ltnp | rg ':9457'
curl -sS http://127.0.0.1:9457/json/version
curl -sS http://127.0.0.1:9457/json/list

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
