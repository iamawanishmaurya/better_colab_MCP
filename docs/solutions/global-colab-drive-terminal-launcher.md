# Solution: Global colab-drive-terminal launcher

Links back to: [Problem: Global colab-drive-terminal command missing](../problems/2026-06-07-global-colab-drive-terminal-command-missing.md)

## What Failed

Running from `~` failed:

```bash
uv run colab-drive-terminal
```

`uv` had no project context and no executable named `colab-drive-terminal` on PATH.

## What Worked

Created a user-level launcher at:

```text
/home/astra/.local/bin/colab-drive-terminal
```

Launcher contents:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo="/home/astra/codex/Google-Colab/better_colab_MCP"
exec uv --directory "$repo" run colab-drive-terminal "$@"
```

Then made it executable:

```bash
chmod +x /home/astra/.local/bin/colab-drive-terminal
```

## Why It Worked

`/home/astra/.local/bin` is already on PATH. The launcher gives the command a stable global executable name and always runs the repo project entry point through `uv --directory`, so it works even when the current directory is `~`.

## Commands Run

```bash
chmod +x /home/astra/.local/bin/colab-drive-terminal
/home/astra/.local/bin/colab-drive-terminal --help
uv run colab-drive-terminal --help
```

Result:

```text
Open a Drive-backed Colab terminal through MCP.
```
