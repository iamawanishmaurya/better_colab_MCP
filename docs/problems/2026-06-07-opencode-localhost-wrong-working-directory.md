# OpenCode Localhost Command Run From Wrong Working Directory

## Exact Error

```text
/home/astra/.local/share/uv/python/cpython-3.11.9-linux-x86_64-gnu/bin/python3.11: can't open file '/home/astra/scripts/colab_opencode_localhost.py': [Errno 2] No such file or directory
```

## Reproduction Steps

1. Start in the home directory:

   ```bash
   cd ~
   ```

2. Run:

   ```bash
   uv run python scripts/colab_opencode_localhost.py \
     --terminal-backend ghosttown \
     --ghosttown-session-mode tmux \
     --ghosttown-tmux-session opencode
   ```

3. Python looks for `/home/astra/scripts/colab_opencode_localhost.py` and fails.

## Environment

- Shell working directory: `/home/astra`
- Repository path: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Date: `2026-06-07`

## First Hypothesis

The command is valid only when run from the repository root, or when the script path is given as an absolute path.
