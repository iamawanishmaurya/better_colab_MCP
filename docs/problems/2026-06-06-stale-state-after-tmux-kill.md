# Problem: stale state file after tmux MCP shutdown

## Exact error

After killing the `colab-mcp-live` tmux session, `/tmp/colab-mcp-current.json` remained and still pointed to PID `2906369`, but the process no longer existed.

Process and port checks:

```text
ps -p 2906369 -o pid,ppid,stat,cmd
    PID    PPID STAT CMD

ss -ltnp | rg ':43475' || true
<no output>
```

## Reproduction steps

1. Start `uv run colab-mcp` inside tmux session `colab-mcp-live`.
2. Kill the tmux session with `tmux kill-session -t colab-mcp-live`.
3. Check `/tmp/colab-mcp-current.json`.
4. Check the recorded PID and port.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- tmux session: `colab-mcp-live`
- Stale MCP state path: `/tmp/colab-mcp-current.json`

## First hypothesis

The server process was terminated by tmux before its async cleanup removed the state file.
