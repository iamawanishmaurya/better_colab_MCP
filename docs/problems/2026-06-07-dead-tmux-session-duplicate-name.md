# Dead Tmux Session Duplicate Name

- Date: 2026-06-07
- Area: Live shell-mode validation

## Exact Error

```text
duplicate session: colab-drive-terminal-cdp
179277 cd 1
```

## Reproduction Steps

1. Let a tmux session die after a failed bridge run.
2. Start a new tmux session with the same name:

   ```bash
   tmux new-session -d -s colab-drive-terminal-cdp '...'
   ```

3. Observe that tmux still reserves the dead session name until it is killed.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- tmux session: `colab-drive-terminal-cdp`
- Dead pane status: `179277 cd 1`

## First Hypothesis

The previous failed bridge left a dead tmux session object. Kill the dead session before relaunching with the same name.
