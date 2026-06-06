# Generated Setup Cell Compile Check Used Wrong Helper Argument

## Exact Error

```text
Traceback (most recent call last):
  File "<stdin>", line 10, in <module>
TypeError: setup_cell_code() got an unexpected keyword argument 'auth_token'
```

## Reproduction Steps

1. From `/home/astra/codex/Google-Colab/better_colab_MCP`, run:

   ```bash
   PYTHONPATH=scripts uv run python - <<'PY'
   from colab_opencode_web_terminal import setup_cell_code

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

2. Python imports the helper successfully, then fails because the helper does not accept `auth_token`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Command runner: `PYTHONPATH=scripts uv run python`
- Helper: `colab_opencode_web_terminal.setup_cell_code`
- Date: `2026-06-07`

## First Hypothesis

The ad hoc verification command used a stale or guessed parameter name. The helper signature should be inspected and the compile check should be rerun using the actual token parameter.
