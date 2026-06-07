# Problem: Global colab-drive-terminal command missing

## Exact Error

```text
uv run colab-drive-terminal
error: Failed to spawn: `colab-drive-terminal`
  Caused by: No such file or directory (os error 2)
```

## Reproduction Steps

1. Start from the home directory:

   ```bash
   cd ~
   ```

2. Run:

   ```bash
   uv run colab-drive-terminal
   ```

3. `uv` cannot spawn `colab-drive-terminal` because the current directory is not the `better_colab_MCP` project and no global launcher exists.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Shell: `zsh`
- Date: `2026-06-07T12:53:06+05:30`
- PATH includes `/home/astra/.local/bin`
- `uv` path: `/usr/bin/uv`

## First Hypothesis

The `colab-drive-terminal` console script is available through this repo's Python project environment, but `uv run` from `~` has no project context. A small executable in `/home/astra/.local/bin` should delegate into the repo with `uv --directory /home/astra/codex/Google-Colab/better_colab_MCP run colab-drive-terminal`.
