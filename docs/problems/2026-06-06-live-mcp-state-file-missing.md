# Problem: live MCP state file missing after tmux startup

## Exact error

The startup command created the tmux session but did not produce `/tmp/colab-mcp-current.json` within the initial wait.

Command output:

```text
alien-dashboard: 1 windows (created Sat Jun  6 13:29:54 2026)
colab: 1 windows (created Fri Jun  5 12:19:31 2026)
colab-mcp-live: 1 windows (created Sat Jun  6 13:30:14 2026)
colabfix: 1 windows (created Fri Jun  5 23:24:04 2026)
part31-monitor: 1 windows (created Sat Jun  6 09:20:01 2026)
tmatecheck: 1 windows (created Fri Jun  5 23:35:51 2026)
missing-state-file
```

## Reproduction steps

1. Work in `/home/astra/codex/Google-Colab/better_colab_MCP`.
2. Start tmux session `colab-mcp-live` with:

```shell
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_CONNECTION_TIMEOUT=180 \
COLAB_MCP_EDGE_CDP_PORT=9333 \
uv run colab-mcp
```

3. Wait two seconds.
4. Check `/tmp/colab-mcp-current.json`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- tmux session: `colab-mcp-live`
- Browser command: `google-chrome-stable`
- Browser user data directory: `/home/astra/.config/google-chrome`
- Browser profile directory: `Default`
- CDP port: `9333`

## First hypothesis

The MCP server may have failed immediately inside tmux, or `mcp.run_async()` may need a real MCP stdio client and exits when started as a standalone tmux process.
