# Opencode install script preview hang

- Timestamp: 2026-06-06T14:23:00+05:30
- Problem file: `docs/problems/2026-06-06-opencode-install-script-preview-hang.md`

## What Failed

The notebook-cell bridge hung after this command:

```sh
curl -fsSL https://opencode.ai/install | sed -n '1,120p'
```

The bridge did not return partial output because it waits for the remote cell subprocess to finish.

## What Worked

The stuck Colab execution was interrupted from the visible Chrome window with `Ctrl+M`, then `I`. After that, the install flow was moved to `scripts/colab_opencode_web_terminal.py`, which uses bounded curl timeouts and starts Opencode through `ttyd` instead of trying to run an interactive TUI through a notebook cell.

## Why It Worked

Interrupting released Colab's single notebook execution slot. Bounded curl prevents another indefinite network wait, and `ttyd` provides a real PTY-backed browser terminal for Opencode.

## Commands Run

```sh
tmux send-keys -t colab-cell-terminal "curl -fsSL https://opencode.ai/install | sed -n '1,120p'" C-m
tmux capture-pane -t colab-cell-terminal -p -S -240
tmux send-keys -t colab-cell-terminal C-c
hyprctl dispatch workspace 5
hyprctl dispatch focuswindow address:0x5790046a0d60
ydotool key 1:1 1:0 29:1 50:1 50:0 29:0 23:1 23:0
uv run python scripts/colab_opencode_web_terminal.py --setup-timeout 1200 --install-timeout 600
```
