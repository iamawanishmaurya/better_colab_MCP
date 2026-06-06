# pkill Browser Cleanup Pattern Self-Match

- Date: 2026-06-07
- Area: Live smoke cleanup

## Exact Error

```text
Cleanup command exited with code -1 and no stderr while running:
pkill -f 'remote-debugging-port=9460|user-data-dir=/tmp/colab-mcp-opencode-tmux-profile-copy' || true
```

## Reproduction Steps

1. Run the broad `pkill -f` command from a shell whose command line contains the same pattern.
2. Observe the cleanup command terminate abnormally before printing the follow-up socket checks.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Shell: zsh through the command runner
- Target browser: isolated headless Chrome on CDP port `9460`

## First Hypothesis

The `pkill -f` pattern matched the shell command that was executing the cleanup itself. Future cleanup should enumerate matching PIDs first and pass exact PIDs to `kill`, avoiding a self-match.
