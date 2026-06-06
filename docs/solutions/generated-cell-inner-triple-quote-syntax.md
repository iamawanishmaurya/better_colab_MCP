# Generated Cell Inner Triple Quote Syntax

- Problem: [docs/problems/2026-06-06-generated-cell-inner-triple-quote-syntax.md](../problems/2026-06-06-generated-cell-inner-triple-quote-syntax.md)

## What Failed

An inner triple-quoted bash script string inside the generated Colab setup cell closed the outer `setup_cell_code()` f-string.

## What Worked

The recovery shell script content now uses parenthesized normal string literals rather than an inner triple-quoted string.

## Why It Worked

Normal string literals do not conflict with the outer triple-quoted generated-cell string.

## Commands Run

```bash
uv run python scripts/colab_opencode_web_terminal.py --help
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code
for backend in ('ttyd', 'ghosttown'):
    code = setup_cell_code(port=7681, cwd='/content', install_timeout=600, terminal_backend=backend)
    compile(code, f'<setup-{backend}>', 'exec')
PY
```
