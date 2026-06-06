# Tmux cell terminal startup timeout

- Timestamp: 2026-06-06T13:48:37+05:30
- Problem file: `docs/problems/2026-06-06-tmux-cell-terminal-startup-timeout.md`

## What Failed

The first tmux readiness wait loop stopped after 180 seconds while the pane still only showed:

```text
Connecting Colab MCP browser session...
```

That made the bridge look stuck even though the browser-side Colab handoff later completed.

## What Worked

The existing tmux session eventually connected, created a backing Colab code cell, and accepted commands. After that, the bridge was updated to make this path more reliable and easier to diagnose:

- The default bridge connection timeout is now 600 seconds.
- Chrome is opened with `--new-window` by default so the scratch notebook navigation is more visible.
- The bridge prints a redacted connection URL and periodic wait status while polling.
- `--print-url`, `--browser-open-mode`, `--connect-poll-interval`, and `--connect-status-interval` flags were added.
- Invalid timeout and interval values now fail fast.

## Why It Worked

The live MCP server and Colab browser extension path were functional; the failure was caused by a slow browser/Colab connection handoff combined with no progress output. Waiting longer proved the connection could complete, and the code change makes future starts visibly diagnosable instead of appearing frozen.

## Commands Run

```sh
tmux capture-pane -t colab-cell-terminal -p -S -200
tmux list-panes -t colab-cell-terminal -F '#{pane_pid} #{pane_current_command} #{pane_dead} #{pane_dead_status}'
ps -ef | rg 'colab_cell_terminal|colab-mcp|better_colab_MCP|remote-debugging-port=9333'
tail -200 /tmp/colab-mcp-cell-terminal.log 2>/dev/null || true
ls -l /tmp/colab-mcp-current.json 2>/dev/null && sed -n '1,120p' /tmp/colab-mcp-current.json 2>/dev/null || true
tmux send-keys -t colab-cell-terminal "pwd" C-m
tmux capture-pane -t colab-cell-terminal -p -S -80
tmux send-keys -t colab-cell-terminal "printf 'tmux-cell-terminal-ok-20260606\\n'" C-m
tmux capture-pane -t colab-cell-terminal -p -S -80
```
