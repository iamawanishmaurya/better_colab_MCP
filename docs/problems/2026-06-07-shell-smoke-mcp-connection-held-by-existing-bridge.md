# Shell Smoke MCP Connection Held By Existing Bridge

- Date: 2026-06-07
- Area: Live shell-mode validation

## Exact Error

The one-shot shell-mode smoke stayed at:

```text
Connecting Colab MCP browser session...
```

while an existing Opencode localhost bridge was still active on `127.0.0.1:8768`.

Live state during the hang:

```text
127.0.0.1:9463 LISTEN chrome
127.0.0.1:8768 LISTEN python3
```

The new MCP state file showed a fresh proxy server waiting for browser attachment:

```json
{
  "host": "127.0.0.1",
  "port": 34617,
  "token": "<redacted>",
  "scratchUrl": "https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>&mcpProxyPort=34617",
  "pid": 155579
}
```

## Reproduction Steps

1. Keep the existing signed-CDP Opencode bridge alive on `127.0.0.1:8768`.
2. Start a second one-shot shell-mode smoke using the same Colab browser/CDP profile:

   ```bash
   uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --terminal-command shell --ghosttown-session-mode tmux --ghosttown-tmux-session drive-terminal --no-require-drive --local-port 8770 --colab-port 7686 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --exit-after-smoke --log-file /tmp/colab-mcp-shell-mode-smoke-mcp.log
   ```

3. Observe that the second launcher remains at `Connecting Colab MCP browser session...`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Existing live bridge: `127.0.0.1:8768`
- New shell smoke local port: `8770`
- New shell smoke Colab port: `7686`
- Browser CDP port: `9463`
- Browser profile copy: `/tmp/colab-mcp-opencode-realcopy-profile`

## First Hypothesis

The active browser page already has a live Colab MCP frontend connection for the existing bridge. The shell-mode smoke should be validated after freeing that existing connection, or by using a separate browser/profile/tab that is not already connected.
