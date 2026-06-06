# Solution: ruff missing sys import

## Linked problem

- [Problem: ruff missing sys import](../problems/2026-06-06-ruff-missing-sys-import.md)

## What failed

`uv run ruff check .` failed because `session.py` referenced `sys.stderr` without importing `sys`.

## What worked

Added `import sys` to `src/colab_mcp/session.py`.

## Why it worked

The optional connection URL printing path writes to `sys.stderr`, so the module must import `sys`.

## Commands run

```shell
uv run ruff check .
```

## Result

The undefined-name lint error is fixed.
