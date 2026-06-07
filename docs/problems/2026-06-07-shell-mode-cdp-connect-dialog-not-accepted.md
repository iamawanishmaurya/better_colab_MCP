# Shell Mode CDP Connect Dialog Not Accepted

- Date: 2026-06-07
- Area: Live shell-mode validation

## Exact Error

The shell-mode bridge remained at:

```text
Connecting Colab MCP browser session...
```

After freeing the existing bridge, CDP inspection showed the browser was signed in and had the correct new token/port, but the local MCP approval dialog was still open:

```json
{
  "ready": "complete",
  "account": "Google Account: nothumanatall (canbehumanagain@gmail.com)",
  "serviceConnected": false,
  "outerConnected": false,
  "innerTransport": "undefined",
  "sessionPort": "44133",
  "bodyHead": "... Terminal\\nCancelConnect"
}
```

## Reproduction Steps

1. Stop the existing localhost bridge so ports `8768` and `8770` are free.
2. Start shell mode through the signed copied Chrome profile:

   ```bash
   tmux new-session -d -s colab-drive-terminal-cdp 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --terminal-command shell --ghosttown-session-mode tmux --ghosttown-tmux-session drive-terminal --no-require-drive --local-port 8768 --colab-port 7686 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --log-file /tmp/colab-mcp-shell-mode-live-mcp.log > /tmp/colab-mcp-shell-mode-live.log 2>&1'
   ```

3. Poll `/tmp/colab-mcp-shell-mode-live.log`.
4. Inspect the Colab page through CDP.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser CDP port: `9463`
- Browser account: `canbehumanagain@gmail.com`
- Local port requested: `8768`
- Colab port requested: `7686`
- Terminal command: `shell`

## First Hypothesis

`localColabMcpService.connect()` can open Colab's local MCP approval dialog without accepting it. The CDP attach helper must handle the dialog by clicking its `Connect` button, then verify the inner MCP server transport.
