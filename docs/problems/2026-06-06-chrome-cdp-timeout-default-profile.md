# Problem: Chrome CDP timeout with Default profile

## Exact error

```json
{
  "ok": false,
  "error": "Timed out waiting for browser CDP on port 9333."
}
```

## Reproduction steps

1. Start the live MCP server in tmux session `colab-mcp-live`.
2. Confirm `/tmp/colab-mcp-current.json` exists.
3. Run:

```shell
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_CONNECTION_TIMEOUT=180 \
uv run colabctl --port 9333 --browser-command google-chrome-stable connect \
  --profile /home/astra/.config/google-chrome \
  --profile-directory Default \
  --timeout 180 \
  --allow-ambiguous
```

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser command: `google-chrome-stable`
- User data directory: `/home/astra/.config/google-chrome`
- Profile directory: `Default`
- CDP port: `9333`
- MCP tmux session: `colab-mcp-live`

## First hypothesis

Chrome may already be running for `/home/astra/.config/google-chrome` without remote debugging. In that case, a new `google-chrome-stable --remote-debugging-port=9333 --user-data-dir=/home/astra/.config/google-chrome --profile-directory=Default` command can be forwarded to the existing Chrome process and the new remote-debugging flag is ignored, so CDP never opens on port `9333`.
