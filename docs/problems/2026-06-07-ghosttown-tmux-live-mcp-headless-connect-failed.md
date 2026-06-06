# Ghost Town tmux Live Smoke MCP Headless Connect Failed

- Date: 2026-06-07
- Area: Live Ghost Town tmux-mode localhost smoke

## Exact Error

```text
RuntimeError: Colab MCP did not connect: opened={'result': False} info={'host': '127.0.0.1', 'port': 33517, 'token': '<redacted>', 'scratchUrl': 'https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>&mcpProxyPort=33517', 'pid': 3789738, 'connected': False, 'browser': {'command': 'google-chrome-stable', 'userDataDir': '/tmp/colab-mcp-opencode-profile-copy', 'profileDirectory': 'Default', 'headless': True, 'copyProfile': {'enabled': True, 'sourceUserDataDir': '/home/astra/.config/google-chrome', 'targetUserDataDir': '/tmp/colab-mcp-opencode-profile-copy'}, 'cookieFile': {'configured': False}, 'cdpPort': '9458', 'urlContains': 'colab.research.google.com', 'connectionTimeoutSeconds': 240.0, 'printConnectionUrl': False, 'compatibilityEnv': {'edgePath': None, 'edgeProfile': None}}}
```

## Reproduction Steps

1. Start the Ghost Town tmux localhost bridge:

   ```bash
   tmux new-session -d -s colab-opencode-ghosttown-tmux 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --no-require-drive --colab-port 7683 --local-port 8767 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --log-file /tmp/colab-mcp-opencode-ghosttown-tmux-mcp.log > /tmp/colab-mcp-opencode-ghosttown-tmux.log 2>&1'
   ```

2. Poll `/tmp/colab-mcp-opencode-ghosttown-tmux.log`.
3. Observe the bridge time out while waiting for Colab MCP browser connection.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Local tmux session: `colab-opencode-ghosttown-tmux`
- Browser command: `google-chrome-stable`
- Browser mode: copied-profile headless Chrome
- CDP port: `9458`
- Colab port: `7683`
- Local proxy port: `8767`

## First Hypothesis

The copied headless Chrome profile did not connect to the Colab MCP frontend within the 240 second timeout. This is a browser/session connection failure before the generated tmux setup cell runs, not evidence that Ghost Town tmux mode failed.
