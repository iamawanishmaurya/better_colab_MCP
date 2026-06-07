# Wrapped Tmux Command Stale Log

## Exact Error

The command pasted into the terminal wrapped inside the single-quoted tmux command, splitting the repository path and long option names. The tmux pane exited immediately:

```text
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_id} #{pane_pid} #{pane_current_command} dead=#{pane_dead} status=#{pane_dead_status}'
%76 361779 cd dead=1 status=127
```

The visible traceback was read from an older log file instead of the failed 10:05 run:

```text
RuntimeError: Colab runtime did not connect: {'text': '<urlopen error [Errno 111] Connection refused>'}
```

The current run did not leave the expected listeners:

```text
curl -sS http://127.0.0.1:9463/json/version
curl: (7) Failed to connect to 127.0.0.1 port 9463 after 1 ms: Could not connect to server

curl -sS http://127.0.0.1:8768/new
curl: (7) Failed to connect to 127.0.0.1 port 8768 after 0 ms: Could not connect to server
```

The logs being tailed were stale:

```text
2026-06-07 09:56:57.052302429 +0530 1432 /tmp/colab-mcp-shell-mode-live.log
2026-06-07 09:52:48.768707796 +0530 3305 /tmp/colab-mcp-shell-mode-live-mcp.log
```

## Reproduction Steps

1. Paste the long `tmux new-session` command with line wraps inside the single-quoted command body.
2. The path is split around `/home/astra/codex/Google-Colab/` and `better_colab_MCP`.
3. Tmux starts, executes `cd /home/astra/codex/Google-Colab/`, then tries to run `better_colab_MCP` as a command.
4. The pane exits with status `127`.
5. `tail -f /tmp/colab-mcp-shell-mode-live.log` shows the previous runtime traceback, because the new command never refreshed that file.

## Environment

- Timestamp: `2026-06-07T10:08:17+05:30`
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- tmux session: `colab-drive-terminal-cdp`
- Intended local port: `8768`
- Intended Colab port: `7686`
- Intended CDP port: `9463`
- Intended terminal mode: `shell`
- Intended copied Chrome profile: `/tmp/colab-mcp-opencode-realcopy-profile`

## First Hypothesis

The immediate 10:05 failure is command transport fragility, not a new Colab runtime failure. The long single-quoted tmux command is too easy to corrupt through terminal wrapping, and reusing fixed log names makes stale failures look current. A launcher script should build the command with shell arrays, create fresh per-run logs, wait for localhost before opening `/new`, and keep the Drive-backed shell/opencode mode selectable.
