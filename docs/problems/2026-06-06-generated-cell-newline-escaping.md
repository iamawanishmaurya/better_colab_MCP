# Generated Cell Newline Escaping

- Timestamp: 2026-06-06T17:09:05+05:30
- Environment: Local generated-cell validation with `PYTHONPATH=scripts`.

## Exact Error

```text
File "<setup-ttyd>", line 137
    "#!/usr/bin/env bash
    ^
SyntaxError: unterminated string literal (detected at line 137)
```

## Reproduction Steps

1. Compile the generated Colab setup cell:
   ```bash
   PYTHONPATH=scripts uv run python - <<'PY'
   from colab_opencode_web_terminal import setup_cell_code
   code = setup_cell_code(port=7681, cwd='/content', install_timeout=600, terminal_backend='ttyd')
   compile(code, '<setup-ttyd>', 'exec')
   PY
   ```
2. The generated code contains a quoted string split by actual newlines.

## First Hypothesis

The outer f-string interpreted `\n` in the inner bash script string while generating the cell. The generated Python code needs escaped backslash-newline sequences (`\\n`) inside those inner string literals.
