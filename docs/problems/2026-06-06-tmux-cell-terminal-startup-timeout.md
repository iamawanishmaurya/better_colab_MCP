# Tmux cell terminal startup timeout

- Timestamp: 2026-06-06T13:45:26+05:30
- Problem slug: tmux-cell-terminal-startup-timeout

## Exact Error

The tmux-backed Colab cell terminal did not reach the ready prompt within the 180 second wait loop. The captured pane output was:

```text
Connecting Colab MCP browser session...
```

No `Ready. Backing Colab cell:` line appeared before the timeout.

## Reproduction Steps

1. From `/home/astra/codex/Google-Colab/better_colab_MCP`, start the bridge in tmux:

   ```sh
   tmux has-session -t colab-cell-terminal 2>/dev/null && tmux kill-session -t colab-cell-terminal || true
   tmux new-session -d -s colab-cell-terminal "cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_cell_terminal.py"
   ```

2. Poll for readiness:

   ```sh
   for i in $(seq 1 90); do
     out=$(tmux capture-pane -t colab-cell-terminal -p -S -80 2>/dev/null || true)
     printf '%s' "$out" | rg -q 'Ready\. Backing Colab cell:' && break
     sleep 2
   done
   tmux capture-pane -t colab-cell-terminal -p -S -80 | sed -n '1,120p'
   ```

3. Observe that the pane still only shows `Connecting Colab MCP browser session...`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- Shell: `zsh`
- tmux: installed and usable
- Browser command: default bridge setting, `google-chrome-stable`
- Chrome user data dir: `/home/astra/.config/google-chrome`
- Chrome profile: `Default`
- Prior live MCP status: direct FastMCP client-managed probe connected and ran a Colab code cell successfully.

## First Hypothesis

The bridge is blocked while waiting for the browser-side MCP connection. The likely causes are either that the scratch URL was not opened/navigated in the already-running Chrome profile, or that the bridge process is using a different generated MCP URL than the currently visible Colab scratch page.
