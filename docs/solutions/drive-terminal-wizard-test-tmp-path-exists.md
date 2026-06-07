# Solution: Drive terminal wizard test tmp_path already exists

Links back to: [Problem: Drive terminal wizard test tmp_path already exists](../problems/2026-06-07-drive-terminal-wizard-test-tmp-path-exists.md)

## What Failed

The new wizard test helper called `path.mkdir(parents=True)` on pytest's `tmp_path`. Pytest creates `tmp_path` before the test runs, so the helper raised `FileExistsError`.

## What Worked

Changed the helper to:

```python
path.mkdir(parents=True, exist_ok=True)
```

## Why It Worked

The test helper only needs to ensure the directory exists before writing Chrome's `Local State` fixture. Allowing an existing directory matches pytest's `tmp_path` lifecycle.

## Commands Run

```bash
uv run pytest tests/drive_terminal_wizard_test.py -q
```

Result:

```text
4 passed
```
