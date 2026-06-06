# Opencode Localhost Colab Proxy Root 404

## Exact Error

The localhost bridge parsed the Colab proxy URL and started a local proxy, but the smoke request returned `404`:

```text
Opencode Colab proxy URL: https://7681-m-s-kkb-usc1a0-mxqx8jh3ge8x-a.us-central1-0.prod.colab.dev
Localhost URL: http://127.0.0.1:8765
Localhost smoke: {"bodyPrefix": "", "ok": false, "status": 404}
RuntimeError: Localhost smoke failed: {'ok': False, 'status': 404, 'bodyPrefix': ''}
```

Opencode and ttyd were running in Colab:

```text
opencode --version
1.16.2
ttyd --version
ttyd version 1.6.3
COLAB_OPENCODE_RESULT {"ok": true, "pid": "42986", "port": 7681, "portOpen": true}
```

## Reproduction Steps

1. Ran:

```bash
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
```

2. The script connected MCP, connected the runtime, started ttyd, extracted `proxyUrl`, started a local reverse proxy, and smoked `http://127.0.0.1:8765`.

## Environment

- Repo: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- CDP port: `9458`
- Localhost port: `8765`
- Colab ttyd port: `7681`
- Colab proxy URL shape: `https://7681-...prod.colab.dev`

## First Hypothesis

The Colab kernel proxy URL returned by `google.colab.kernel.proxyPort(PORT)` may require a specific path or browser-origin handling that is different from simply proxying `/` to the returned origin root. The local proxy should inspect candidate URL forms before treating the root `404` as a ttyd failure.
