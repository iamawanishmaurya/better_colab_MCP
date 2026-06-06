# Changelog

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
