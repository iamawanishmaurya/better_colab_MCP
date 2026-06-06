# Solution: stale state file after tmux MCP shutdown

## Linked problem

- [Problem: stale state file after tmux MCP shutdown](../problems/2026-06-06-stale-state-after-tmux-kill.md)

## What failed

Killing the tmux MCP server left `/tmp/colab-mcp-current.json` pointing at a dead PID and inactive port.

## What worked

Verified the recorded PID and port were inactive, then removed the stale state file.

## Why it worked

The state file is only valid while the recorded PID is alive and the recorded port is listening. Once both checks failed, removing it avoided confusing future `colabctl` or live-client tests.

## Commands run

```shell
tmux kill-session -t colab-mcp-live 2>/dev/null || true
ps -p 2906369 -o pid,ppid,stat,cmd || true
ss -ltnp | rg ':43475' || true
rm -f /tmp/colab-mcp-current.json
```

## Result

The stale state file was removed.
