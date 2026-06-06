# Solution: Opencode Localhost Gzip Double Decode

Links back to: `docs/problems/2026-06-06-opencode-localhost-gzip-double-decode.md`

## What Failed

The local reverse proxy used aiohttp's default upstream auto-decompression, then forwarded the original `Content-Encoding: gzip` header. The localhost smoke client tried to decode the already-decoded body as gzip.

## What Worked

The upstream proxy `ClientSession` now uses `auto_decompress=False`, preserving encoded bytes and matching response headers. The script also cleans up the local proxy runner when smoke testing raises.

## Why It Worked

Reverse proxies must either preserve compressed bytes and compression headers together, or decode bytes and strip compression headers. Preserving bytes is simpler and works for browsers and the smoke client.

## Commands Run

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
