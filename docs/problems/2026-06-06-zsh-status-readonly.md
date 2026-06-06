# zsh Read-Only Status Variable During Supervisor Poll

- Timestamp: 2026-06-06T16:41:18+05:30
- Environment: zsh shell in `/home/astra/codex/Google-Colab/better_colab_MCP` while waiting for the restarted `colab-opencode-supervisor` tmux session to reach `running`.

## Exact Error

```text
zsh:1: read-only variable: status
```

## Reproduction Steps

1. Run a zsh command that assigns to a variable named `status`:
   ```bash
   for i in {1..60}; do status=$(python -c 'print("starting")'); echo "$status"; done
   ```
2. zsh rejects the assignment because `status` is a reserved read-only parameter for the last command exit status.

## First Hypothesis

The poll script used `status` as a normal shell variable name. zsh reserves that name, so the fix is to rerun the poll with a non-reserved variable such as `state_value`.
