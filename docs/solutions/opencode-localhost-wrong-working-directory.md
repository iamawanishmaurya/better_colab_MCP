# OpenCode Localhost Wrong Working Directory

Problem file: [../problems/2026-06-07-opencode-localhost-wrong-working-directory.md](../problems/2026-06-07-opencode-localhost-wrong-working-directory.md)

## What Failed

The launcher was run from `~`, so Python looked for:

```text
/home/astra/scripts/colab_opencode_localhost.py
```

That file does not exist.

## What Worked

Run the script from the repository root or use an absolute script path.

## Why It Worked

The script is stored at:

```text
/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py
```

`uv run python scripts/...` resolves `scripts/...` relative to the current working directory.

## Commands Run

```bash
pwd
git status --short --branch
tmux new-session -d -s colab-opencode-ghosttown-tmux-start 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --local-port 8767 --colab-port 7684 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 180 --log-file /tmp/colab-mcp-opencode-ghosttown-tmux-start-mcp.log > /tmp/colab-mcp-opencode-ghosttown-tmux-start.log 2>&1'
```
