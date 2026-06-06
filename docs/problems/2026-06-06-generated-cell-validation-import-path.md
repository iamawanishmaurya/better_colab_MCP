# Generated Cell Validation Import Path

- Timestamp: 2026-06-06T17:08:19+05:30
- Environment: Local validation with `uv run python - <<'PY'` from the repository root.

## Exact Error

```text
ModuleNotFoundError: No module named 'colab_visible_connect'
```

## Reproduction Steps

1. Import the script as if `scripts` were a namespace package:
   ```bash
   uv run python - <<'PY'
   from scripts.colab_opencode_web_terminal import setup_cell_code
   PY
   ```
2. The import fails because `colab_opencode_web_terminal.py` imports sibling script `colab_visible_connect.py` by script-local name.

## First Hypothesis

The validation command used an import style that does not match script execution. Running validation with `PYTHONPATH=scripts` or inserting the `scripts/` directory into `sys.path` should match the intended execution context.
