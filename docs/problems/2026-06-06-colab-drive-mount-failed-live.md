# Colab Drive Mount Failed During Live Ghost Town Test

- Date: 2026-06-06
- Area: Opencode Colab Ghost Town setup

## Exact Error

```text
ValueError: mount failed

RuntimeError: Google Drive mount failed. Complete the Colab Drive authorization prompt and rerun setup.

RuntimeError: Opencode setup did not emit COLAB_OPENCODE_RESULT.
```

## Reproduction Steps

1. Start the localhost bridge with the Ghost Town backend and required Google Drive persistence:

   ```bash
   uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --colab-port 7682 --local-port 8766 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 240 --log-file /tmp/colab-mcp-opencode-ghosttown-mcp.log
   ```

2. Let the script connect to the existing visible Colab MCP browser session.
3. Wait for the setup cell to run `google.colab.drive.mount("/content/drive", force_remount=False)`.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Python runner: `uv run`
- Browser path: existing visible Colab MCP browser session
- Colab runtime: Python 3.12 notebook kernel
- Terminal backend: `ghosttown`
- Local proxy port: `127.0.0.1:8766`
- Colab service port: `7682`

## First Hypothesis

The Google Drive mount requires an interactive Colab authorization step in the visible browser. The automated setup cell correctly stops when Drive is required, but that strict mode prevents automated Ghost Town/OpenCode smoke validation until Drive is authorized or a non-strict fallback is requested.
