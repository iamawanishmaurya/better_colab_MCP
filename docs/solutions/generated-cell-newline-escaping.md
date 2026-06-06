# Generated Cell Newline Escaping

- Problem: [docs/problems/2026-06-06-generated-cell-newline-escaping.md](../problems/2026-06-06-generated-cell-newline-escaping.md)

## What Failed

The generated Colab code contained an unterminated string because outer string interpolation converted `\n` into actual newlines inside generated Python string literals.

## What Worked

Escape the generated string literals with `\\n` and escape inner quotes around `$HOME`:

```python
script = (
    "#!/usr/bin/env bash\\n"
    "set -euo pipefail\\n"
    "export PATH=\\"$HOME/.opencode/bin:$PATH\\"\\n"
    "cd %s\\n"
    "opencode\\n"
)
```

## Why It Worked

The generated Python code now receives literal backslash-newline sequences inside quoted strings, so it can compile and then write the intended multiline recovery script at runtime.

## Commands Run

```bash
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code
for backend in ('ttyd', 'ghosttown'):
    code = setup_cell_code(port=7681, cwd='/content', install_timeout=600, terminal_backend=backend)
    compile(code, f'<setup-{backend}>', 'exec')
    print(backend, len(code), 'compiled')
PY
```

Result: both `ttyd` and `ghosttown` generated setup cells compiled.
