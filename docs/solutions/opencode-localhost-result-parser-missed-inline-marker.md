# Solution: Opencode Localhost Result Parser Missed Inline Marker

Links back to: `docs/problems/2026-06-06-opencode-localhost-result-parser-missed-inline-marker.md`

## What Failed

`scripts/colab_opencode_localhost.py` looked for `COLAB_OPENCODE_RESULT` only at the start of a line. Colab concatenated IPython Javascript display text before the marker, so the setup succeeded but the parser missed it.

## What Worked

The parser now searches for the marker anywhere in the output and uses `json.JSONDecoder().raw_decode()` to parse the first JSON object after the marker.

## Why It Worked

The result marker is still unique and deterministic, but Colab output formatting is not line-stable when display objects are emitted. Searching the full output keeps the marker contract while tolerating Colab's display preamble.

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
