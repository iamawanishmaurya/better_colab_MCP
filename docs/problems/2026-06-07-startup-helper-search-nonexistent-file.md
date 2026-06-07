# Startup Helper Search Included Nonexistent File

## Exact Error

```text
rg: scripts/colab_mcp_auto_connect.py: No such file or directory (os error 2)
```

## Reproduction Steps

1. From `/home/astra/codex/Google-Colab/better_colab_MCP`, run:

   ```bash
   rg -n "cdp_port|remote-debugging-port|browser_profile_copy_dir|open_chrome|visible_connect" scripts/colab_visible_connect.py scripts/colab_opencode_localhost.py scripts/colab_mcp_auto_connect.py scripts/*.py
   ```

2. `rg` fails because `scripts/colab_mcp_auto_connect.py` does not exist.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Tool: `rg`
- Date: `2026-06-07`

## First Hypothesis

The search command used a guessed filename. The fix is to search only known files or use `rg --files scripts` before naming specific files.
