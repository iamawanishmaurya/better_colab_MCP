# Opencode Localhost Result Parser Missed Inline Marker

## Exact Error

The live Opencode setup succeeded in Colab, but `scripts/colab_opencode_localhost.py` failed to parse the result marker:

```text
RuntimeError: Opencode setup did not emit COLAB_OPENCODE_RESULT.
```

The output did contain the marker, but not at the beginning of a line:

```text
<IPython.core.display.Javascript object><IPython.core.display.Javascript object>COLAB_OPENCODE_RESULT {"logPath": "/content/opencode-ttyd.log", "ok": true, "opencode": "/root/.opencode/bin/opencode", "pid": "42364", "pidPath": "/content/opencode-ttyd.pid", "port": 7681, "portOpen": true, "proxyUrl": "https://7681-m-s-kkb-usc1a0-mxqx8jh3ge8x-a.us-central1-0.prod.colab.dev", "proxyUrlError": null, "ttyd": "/usr/bin/ttyd", "workdir": "/content"}
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

2. The script connected MCP, connected the runtime, confirmed `opencode --version` as `1.16.2`, confirmed `ttyd --version` as `1.6.3`, started ttyd on Colab port `7681`, and then raised the parser error above.

## Environment

- Repo: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- Chrome profile source: `/home/astra/.config/google-chrome` / `Default`
- Copied profile dir: `/tmp/colab-mcp-opencode-profile-copy`
- CDP port: `9458`
- Localhost port: `8765`
- Colab ttyd port: `7681`

## First Hypothesis

The parser is too strict. Colab can concatenate IPython display object text before normal stdout, so `COLAB_OPENCODE_RESULT` must be searched anywhere in the output text rather than only at the start of a split line.
