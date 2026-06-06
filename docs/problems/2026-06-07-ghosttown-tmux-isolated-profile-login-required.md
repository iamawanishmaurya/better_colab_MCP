# Ghost Town tmux Isolated Profile Login Required

- Date: 2026-06-07
- Area: Live Ghost Town tmux-mode localhost smoke

## Exact Error

```text
RuntimeError: Colab runtime did not connect: {'ok': False, 'steps': [], 'warnings': ['Colab login is required in the dedicated MCP browser before connecting a runtime.'], 'before': {'href': 'https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>&mcpProxyPort=35147', 'ready': 'complete', 'loginRequired': True, 'localMcpConnected': True, 'hasNotebook': True, 'hasKernel': True, 'hasRuntime': False, 'hasTerminalConnection': True, 'terminalReady': False, 'kernelLastConnectedTimeMs': -1, ...}, 'browserConnected': True, 'executionBackend': 'colab-browser-cdp', 'status': 'warning'}
```

## Reproduction Steps

1. Start the Ghost Town tmux localhost bridge with an isolated copied profile and CDP port:

   ```bash
   uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --no-require-drive --colab-port 7683 --local-port 8767 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --browser-profile-copy-dir /tmp/colab-mcp-opencode-tmux-profile-copy --cdp-port 9460 --log-file /tmp/colab-mcp-opencode-ghosttown-tmux-mcp.log
   ```

2. Wait for MCP browser connection.
3. Observe `browserConnected: True`, but `loginRequired: True` and runtime connection failure.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser command: `google-chrome-stable`
- Browser mode: copied-profile headless Chrome
- Profile copy path: `/tmp/colab-mcp-opencode-tmux-profile-copy`
- CDP port: `9460`
- Colab port: `7683`
- Local proxy port: `8767`

## First Hypothesis

The isolated copied profile started successfully and connected MCP, but it did not include an authenticated Google/Colab session. The earlier default copied profile was authenticated but is currently occupied by an existing Ghost Town run, so live tmux validation needs either the authenticated profile resources freed or a visible/manual-auth browser path.
