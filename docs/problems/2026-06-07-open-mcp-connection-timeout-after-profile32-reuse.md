# Open MCP Connection Timeout After Profile32 Reuse

## Exact Error

The interrupted non-strict Drive smoke run reused the authenticated `Profile 32` copied profile, but timed out before `open_colab_browser_connection` returned:

```text
Connecting Colab MCP browser session...
...
mcp.shared.exceptions.McpError: Timed out while waiting for response to ClientRequest. Waited 300.0 seconds.
```

The tmux pane exited:

```text
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_id} #{pane_pid} #{pane_current_command} dead=#{pane_dead} status=#{pane_dead_status}'
%80 480278 colab-mcp-colab-drive-terminal-cdp-shell-20260607-103155.runner.sh dead=1 status=1
```

The run left a temporary MCP listener:

```text
127.0.0.1:33639 users:(("colab-mcp",pid=482257,fd=7))
[::1]:37553 users:(("colab-mcp",pid=482257,fd=8))
```

## Reproduction Steps

1. Start a non-strict Drive smoke run after the strict Drive failure:

   ```bash
   ./scripts/launch_colab_drive_terminal.sh shell \
     --profile 'Profile 32' \
     --profile-copy-dir /tmp/colab-mcp-profile32-copy \
     --no-require-drive \
     --no-open \
     --no-tail \
     --exit-after-smoke
   ```

2. Wait for the bridge to call `open_colab_browser_connection`.
3. The MCP client call times out after 300 seconds.

## Environment

- Timestamp: `2026-06-07T10:41:46+05:30`
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Launcher: `scripts/launch_colab_drive_terminal.sh`
- Browser profile: `Profile 32`
- Profile copy dir: `/tmp/colab-mcp-profile32-copy`
- Drive mode: `--no-require-drive`
- Local port: `8768`
- CDP port: `9463`

## First Hypothesis

The previous strict-Drive run successfully connected MCP and runtime, then failed during setup. Reusing the same copied profile immediately afterward may have left stale Colab frontend MCP state, an orphaned local MCP service, or an existing controlled Chrome state that prevented the next `open_colab_browser_connection` request from completing. The future CLI should include stale-session detection and cleanup before reconnecting.
