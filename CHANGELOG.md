# Changelog

## v0.2.0 - 2026-06-06

- Added `scripts/colab_cell_terminal.py`, a tmux-friendly shell bridge backed by a reusable Colab code cell over MCP.
- Added `docs/TMUX_CELL_TERMINAL.md` with attach/start instructions and limitations.
- Added bridge startup diagnostics, redacted connection URL output, explicit Chrome new-window opening, and a longer default browser connection timeout.
- Verified live MCP browser connection, `add_code_cell`, and `run_code_cell` against the local Chrome profile.

## v0.1.0 - 2026-06-06

- Rebased local work onto `404F0X/better_colab_MCP` instead of the Google baseline clone.
- Added Chrome/Chromium-compatible controlled browser startup while preserving legacy Edge env aliases.
- Added `COLAB_MCP_BROWSER_COMMAND`, `COLAB_MCP_BROWSER_USER_DATA_DIR`, `COLAB_MCP_BROWSER_PROFILE`, `COLAB_MCP_CONNECTION_TIMEOUT`, and `COLAB_MCP_PRINT_CONNECTION_URL`.
- Added CLI flags for browser command, browser user data directory, browser profile, connection timeout, and stderr URL printing.
- Added `get_connection_info().browser` diagnostics for command, profile, user data directory, CDP port, URL filter, URL printing, and effective timeout.
- Documented the local `nothumanatall` / `Default` Chrome profile workflow.
- Converted the former Chinese README content to English-only documentation.

## 1.0.1+fork.0

- Forked from the static Colab MCP baseline.
- Added runtime file tools: upload/download/stat/list/delete/mkdir and chunked transfer.
- Added batch notebook/cell helpers: upload/download aliases, replace/patch/find/get cell, batch/range/all execution, status, waiting, and output polling.
- Added environment helpers: get, unset, and `.env` loading with redaction.
- Added background job listing/watching and GPU timestamp sampling/monitoring.
- Added browser userscript tools under `colab_ext.*`.
- Added `colabctl` for Edge CDP control, status, connection repair, browser smoke tests, snapshots, and UI clicks.
