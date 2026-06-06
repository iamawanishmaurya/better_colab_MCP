# Generated Cell Validation Import Path

- Problem: [docs/problems/2026-06-06-generated-cell-validation-import-path.md](../problems/2026-06-06-generated-cell-validation-import-path.md)

## What Failed

Directly importing `scripts.colab_opencode_web_terminal` from the repository root failed because the script imports sibling modules by script-local name.

## What Worked

Run generated-cell validation with `scripts/` on `PYTHONPATH`:

```bash
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code
...
PY
```

## Why It Worked

The scripts are normally executed from the `scripts/` directory context, where sibling imports such as `colab_visible_connect` are resolvable. Adding `scripts/` to `PYTHONPATH` reproduces that import context for validation.

## Commands Run

```bash
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code
for backend in ('ttyd', 'ghosttown'):
    code = setup_cell_code(port=7681, cwd='/content', install_timeout=600, terminal_backend=backend)
    compile(code, f'<setup-{backend}>', 'exec')
PY
```
