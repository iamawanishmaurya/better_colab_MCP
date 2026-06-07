# Problem: Drive terminal wizard test tmp_path already exists

## Exact Error

```text
FAILED tests/drive_terminal_wizard_test.py::test_load_chrome_profiles_reads_names_and_primary_status

FileExistsError: [Errno 17] File exists: '/tmp/pytest-of-astra/pytest-47/test_load_chrome_profiles_read0'

tests/drive_terminal_wizard_test.py:16: in write_local_state
    path.mkdir(parents=True)
```

## Reproduction Steps

1. Add `tests/drive_terminal_wizard_test.py`.
2. Run:

   ```bash
   uv run pytest tests/drive_terminal_wizard_test.py -q
   ```

3. The test helper calls `path.mkdir(parents=True)` on pytest's `tmp_path`, which already exists.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- Command: `uv run pytest tests/drive_terminal_wizard_test.py -q`
- Date: `2026-06-07T11:39:09+05:30`

## First Hypothesis

The test helper is wrong, not the wizard implementation. Pytest creates `tmp_path` before passing it to the test, so the helper should either use `exist_ok=True` or create a child directory under `tmp_path`.
