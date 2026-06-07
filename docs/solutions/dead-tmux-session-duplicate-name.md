# Dead Tmux Session Duplicate Name

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-dead-tmux-session-duplicate-name.md](../problems/2026-06-07-dead-tmux-session-duplicate-name.md)

## What Failed

Starting a new session named `colab-drive-terminal-cdp` failed because a previous dead tmux session with that name still existed.

## What Worked

Kill the named tmux session before relaunching:

```bash
tmux kill-session -t colab-drive-terminal-cdp
```

## Why It Worked

tmux keeps dead panes/sessions addressable until they are explicitly removed. Killing the named session frees the name for a clean launch.

## Commands Run

```bash
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_pid} #{pane_current_command} #{pane_dead}'
tmux kill-session -t colab-drive-terminal-cdp
```
