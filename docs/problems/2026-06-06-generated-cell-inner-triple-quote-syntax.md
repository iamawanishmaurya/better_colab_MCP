# Generated Cell Inner Triple Quote Syntax Error

- Timestamp: 2026-06-06T17:07:07+05:30
- Environment: Local validation with `uv run python` importing `scripts/colab_opencode_web_terminal.py`.

## Exact Error

```text
File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_web_terminal.py", line 229
    set -euo pipefail
             ^^^^^^^^
SyntaxError: invalid syntax
```

## Reproduction Steps

1. Run generated-cell validation:
   ```bash
   uv run python - <<'PY'
   from scripts.colab_opencode_web_terminal import setup_cell_code
   code = setup_cell_code(port=7681, cwd='/content', install_timeout=600, terminal_backend='ghosttown')
   compile(code, '<setup-ghosttown>', 'exec')
   PY
   ```
2. Importing `scripts/colab_opencode_web_terminal.py` fails before the generated code can compile.

## First Hypothesis

An inner triple-quoted bash script string in the generated Colab code prematurely closes the outer triple-quoted Python f-string returned by `setup_cell_code`.
