# Generated Setup Cell Compile Check Missing PYTHONPATH

## Exact Error

```text
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_web_terminal.py", line 18, in <module>
    from colab_visible_connect import visible_connect_attempt
ModuleNotFoundError: No module named 'colab_visible_connect'
```

## Reproduction Steps

1. From `/home/astra/codex/Google-Colab/better_colab_MCP`, run:

   ```bash
   uv run python - <<'PY'
   from scripts.colab_opencode_web_terminal import setup_cell_code
   cases = [
       ("ttyd", {"terminal_backend": "ttyd"}),
       ("ghosttown-direct", {"terminal_backend": "ghosttown"}),
       ("ghosttown-tmux", {"terminal_backend": "ghosttown", "ghosttown_session_mode": "tmux"}),
   ]
   for name, kwargs in cases:
       code = setup_cell_code(auth_token="test-token", project_dir="/content/opencode-project", **kwargs)
       compile(code, f"<{name}>", "exec")
       print(f"{name}: compiled")
   PY
   ```

2. The import fails before generated cell code is compiled.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Command runner: `uv run python`
- Python import target: `scripts.colab_opencode_web_terminal`
- Date: `2026-06-07`

## First Hypothesis

The script imports sibling modules as top-level script modules. The ad hoc verification command imported it as a package module without adding `scripts/` to `PYTHONPATH`, so Python could not resolve `colab_visible_connect`.
