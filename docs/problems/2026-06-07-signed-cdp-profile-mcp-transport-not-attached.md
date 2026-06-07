# Signed CDP Profile MCP Transport Not Attached

- Date: 2026-06-07
- Area: Colab MCP browser automation

## Exact Error

```text
RuntimeError: Colab MCP did not connect: opened={'result': False} info={'host': '127.0.0.1', 'port': 38851, 'token': '<redacted>', 'scratchUrl': 'https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>&mcpProxyPort=38851', 'pid': 79995, 'connected': False, 'browser': {'command': 'google-chrome-stable', 'userDataDir': '/tmp/colab-mcp-opencode-realcopy-profile', 'profileDirectory': 'Default', 'headless': False, 'copyProfile': {'enabled': True, 'sourceUserDataDir': '/home/astra/.config/google-chrome', 'targetUserDataDir': '/tmp/colab-mcp-opencode-realcopy-profile'}, 'cookieFile': {'configured': False}, 'cdpPort': '9463', 'urlContains': 'colab.research.google.com', 'connectionTimeoutSeconds': 240.0, 'printConnectionUrl': False, 'compatibilityEnv': {'edgePath': None, 'edgeProfile': None}}}
```

Additional live CDP inspection before the launcher exited showed:

```json
{
  "localColabMcpServiceConnected": true,
  "colabMcpServerConnected": false,
  "transport": "undefined",
  "tcpConnectionToProxyPort": false
}
```

## Reproduction Steps

1. Close the real Chrome `Default` profile process.
2. Remove the copied profile directory:

   ```bash
   rm -rf /tmp/colab-mcp-opencode-realcopy-profile
   ```

3. Start the Ghost Town tmux bridge with a headed copied `Default` profile and CDP:

   ```bash
   tmux new-session -d -s colab-opencode-ghosttown-cdp-tmux 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 240 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --log-file /tmp/colab-mcp-opencode-realcopy-tmux-mcp.log > /tmp/colab-mcp-opencode-realcopy-tmux.log 2>&1'
   ```

4. Verify CDP is listening on `127.0.0.1:9463` and Colab opens as a signed-in `scratchpad - Colab` page.
5. Inspect the Colab page through CDP and observe that the wrapper reports connected while the underlying server transport is absent.
6. Poll `/tmp/colab-mcp-opencode-realcopy-tmux.log`.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser command: `google-chrome-stable`
- Browser user data dir: `/tmp/colab-mcp-opencode-realcopy-profile`
- Browser profile directory: `Default`
- CDP port: `9463`
- MCP proxy port: `38851`
- Local bridge port requested: `8768`
- Colab terminal port requested: `7685`

## First Hypothesis

Colab accepts the signed-in copied profile and the MCP approval UI can be dismissed through CDP, but the frontend service state does not create or preserve the websocket transport to the local proxy. This is a transport attachment problem after login, not a Google sign-in problem.
