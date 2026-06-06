# Solution: Headless Cookie Mode Anonymous Without Real Cookie File

Links back to: `docs/problems/2026-06-06-headless-cookie-mode-anonymous-without-real-cookie-file.md`

## What Failed

A dummy cookie file successfully exercised the headless cookie import path, but it could not authenticate Google/Colab. The page loaded with `email=anonymous`, `loginRequired=true`, and `connected=false`.

## What Worked

The authenticated copied-profile mode worked. It copied the existing `Default` profile for `canbehumanagain@gmail.com` / `nothumanatall` into `/tmp/colab-mcp-profile-copy-live`, launched headless Chrome from the copy, connected MCP three times, and ran a marker code cell.

## Why It Worked

Headless cookie mode needs a real Google auth source. A dummy cookie only proves CDP cookie injection mechanics. The copied profile includes real browser auth state and avoids the live profile lock, allowing Colab to identify the account in headless Chrome.

## Commands Run

```bash
printf '%s\n' '[{"domain":".colab.research.google.com","name":"COLAB_MCP_DUMMY","value":"dummy","path":"/","secure":true,"sameSite":"no_restriction","expirationDate":1814601961}]' > /tmp/colab-mcp-dummy-cookies.json
chmod 600 /tmp/colab-mcp-dummy-cookies.json

COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_HEADLESS=1 \
COLAB_MCP_BROWSER_COOKIE_FILE=/tmp/colab-mcp-dummy-cookies.json \
COLAB_MCP_BROWSER_USER_DATA_DIR=/tmp/colab-mcp-headless-live-profile \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_EDGE_CDP_PORT=9455 \
COLAB_MCP_CONNECTION_TIMEOUT=240 \
uv run python -

curl -sS http://127.0.0.1:9455/json/version
curl -sS http://127.0.0.1:9455/json/list
python -
kill 3031057 3031066

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
