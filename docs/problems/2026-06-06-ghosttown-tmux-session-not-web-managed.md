# Ghost Town Web UI Would Not Attach Detached tmux Session

- Date: 2026-06-06
- Area: Opencode Colab Ghost Town setup

## Exact Error

```text
No runtime exception occurred yet. Source inspection showed the current implementation starts OpenCode in a detached tmux session, while Ghost Town web mode creates separate web-managed terminal sessions through its own session manager.
```

## Reproduction Steps

1. Generate the Ghost Town setup cell with `terminal_backend="ghosttown"`.
2. Inspect the generated `start_ghosttown()` implementation.
3. Observe that it runs:

   ```bash
   tmux new-session -d -s opencode ...
   ghosttown -p 7682 --http --no-auth
   ```

4. Inspect the published Ghost Town package source and compare command-mode tmux behavior with web server session behavior.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Package inspected: `@seflless/ghosttown`
- Current terminal backend: `ghosttown`

## First Hypothesis

Starting OpenCode in tmux is useful for a CLI attach flow, but it is not sufficient for the Ghost Town browser UI. The web UI should instead start a Ghost Town-managed pseudo-terminal whose shell command launches OpenCode in the persistent project directory.
