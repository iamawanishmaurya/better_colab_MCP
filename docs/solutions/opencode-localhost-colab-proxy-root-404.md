# Solution: Opencode Localhost Colab Proxy Root 404

Links back to: `docs/problems/2026-06-06-opencode-localhost-colab-proxy-root-404.md`

## What Failed

The local reverse proxy forwarded requests to the Colab kernel proxy URL without the browser's runtime proxy cookie. The Colab proxy origin returned `404` for unauthenticated server-side requests.

## What Worked

The bridge now reads the `colab-runtime-proxy-token` cookie from the controlled Chrome iframe target over CDP and forwards it in HTTP and WebSocket requests. It logs only cookie names/domains, not values.

## Why It Worked

Colab's `serve_kernel_port_as_iframe()` loads the proxy URL inside the authenticated browser, which has a host-specific runtime proxy cookie. A laptop-side reverse proxy needs the same cookie to reach ttyd. Once forwarded, local GET returned `200 OK` with ttyd HTML and `ws://127.0.0.1:8765/ws` opened successfully.

## Commands Run

```bash
curl -k -sS -I --max-time 10 https://7681-m-s-kkb-usc1a0-mxqx8jh3ge8x-a.us-central1-0.prod.colab.dev/

python - <<'PY'
# Extracted Colab proxy cookies with CDP Network.getCookies and retried curl with a Cookie header.
PY

uv run python scripts/colab_opencode_localhost.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765 \
  --setup-timeout 1200 \
  --install-timeout 900 \
  --exit-after-smoke

curl -sS --compressed --max-time 10 -D /tmp/opencode-localhost.headers -o /tmp/opencode-localhost.html http://127.0.0.1:8765

python - <<'PY'
from websockets.sync.client import connect
with connect('ws://127.0.0.1:8765/ws', open_timeout=10, close_timeout=2):
    print('websocket_open true')
PY
```
