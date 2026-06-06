# Solution: Headless Existing Profile Locked

Links back to: `docs/problems/2026-06-06-headless-existing-profile-locked.md`

## What Failed

Launching headless Chrome directly against `/home/astra/.config/google-chrome` failed because the visible Chrome process already owned the profile lock. CDP port `9456` never opened.

## What Worked

Added copied-profile mode:

- `COLAB_MCP_BROWSER_COPY_PROFILE=1`
- `COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-profile-copy-live`
- source user data dir `/home/astra/.config/google-chrome`
- profile directory `Default`

The copied profile launched headless on CDP port `9457`, authenticated as `canbehumanagain@gmail.com`, connected MCP in three fresh server cycles, and ran a marker code cell.

## Why It Worked

Chrome cannot safely run two instances against the same locked profile. Copying `Local State` and the selected profile directory into a dedicated headless user-data dir avoids `SingletonLock` while preserving the profile's authentication state. The existing direct CDP connector then sets the MCP token/port and calls `localColabMcpService.connect()` without a manual dialog click.

## Alternatives Evaluated

- Add browser-use as a hard dependency: good profile-copy precedent, but heavier startup, more API drift, and unnecessary because this repo already has CDP primitives.
- Add Playwright as a hard dependency: reliable browser control, but another dependency and duplicate CDP logic.
- Restart visible Chrome with `--remote-debugging-port`: reliable CDP attach, but disruptive to the user's current browser.
- Copy the selected profile and use existing CDP: chosen because it is deterministic, non-disruptive, and keeps the dependency set unchanged.

## Commands Run

```bash
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_HEADLESS=1 \
COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_EDGE_CDP_PORT=9456 \
COLAB_MCP_CONNECTION_TIMEOUT=240 \
uv run python -

ss -ltnp | rg ':9456'
curl -sS http://127.0.0.1:9456/json/version
ps -ef | rg '9456|headless|google-chrome|chrome'
ls -la /home/astra/.config/google-chrome | rg 'Singleton|Lock|Default'
kill 3034648 3034664 3034681

uv run ruff check .
uv run python -m compileall -f src scripts
uv run pytest tests/session_test.py -q

rm -rf /tmp/colab-mcp-profile-copy-live
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_HEADLESS=1 \
COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_BROWSER_COPY_PROFILE=1 \
COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-profile-copy-live \
COLAB_MCP_EDGE_CDP_PORT=9457 \
COLAB_MCP_CONNECTION_TIMEOUT=240 \
uv run python -

ss -ltnp | rg ':9457'
curl -sS http://127.0.0.1:9457/json/version
curl -sS http://127.0.0.1:9457/json/list
kill "$(ss -ltnp | awk '/:9457 / { if (match($0, /pid=[0-9]+/)) { print substr($0, RSTART+4, RLENGTH-4); exit } }')"
```
