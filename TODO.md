# TODO

Goal: make Colab feel like a local development/runtime target through MCP, with browser control used only where Colab UI access is required.

## P0: Connection And Test Harness

- [x] Add `colabctl` CLI entrypoint.
- [x] `colabctl status`: show active MCP server pid, port, token, scratch URL, browser URL, `sessionStorage` token/port, WebSocket state, Colab login email, and runtime connection state.
- [x] `colabctl connect`: open/control Edge, navigate to scratch URL, set/repair `sessionStorage`, reload if needed, and call `window.colab.global.notebook.localColabMcpService.connect()`.
- [x] Detect and report hash/sessionStorage mismatch instead of silently using the wrong MCP server.
- [x] Refuse ambiguous state when multiple `colab-mcp` processes are listening unless the target port/pid is specified.
- [x] Add browser smoke test: call frontend `get_cells` through `colabMcpToolsService.tools[*].toolCallback`.
- [x] Add MCP smoke test: call server `get_connection_info`, `get_cells`, add/run/delete a temporary code cell, and verify stdout.
- [x] Add reliable JS execution helper that passes JavaScript via file/CDP payload, not inline shell strings, to avoid quote corruption.
- [x] Add CI/local test command that runs unit tests plus browser-smoke tests when Edge CDP is available.

## P0: Notebook Upload And Download

- [x] Keep existing `import_notebook(path, cellIndex?, replaceExisting?)` and `export_notebook(path, includeOutputs?)`.
- [x] Add notebook metadata preservation to `export_notebook`: title, Colab metadata, kernelspec, language info, execution counts, outputs, and cell IDs.
- [x] Add `download_notebook(path, includeOutputs=true)` as a clearer alias for local export.
- [x] Add `upload_notebook(path, replaceExisting=false, cellIndex?)` as a clearer alias for local import.
- [x] Add tests for round-tripping a notebook with markdown, code, outputs, metadata, and non-ASCII text.

## P0: Cell Editing

- [x] Keep existing `add_code_cell`, `add_text_cell`, `delete_cell`, `move_cell`, `update_cell`, and `get_cells`.
- [x] Add `replace_cells(cells, replaceExisting=false, cellIndex?)` for bulk notebook edits.
- [x] Add `patch_cell(cellId, source?, metadata?, cellType?)` for partial update without losing metadata when possible.
- [x] Add `get_cell(cellId, includeOutputs=false)` convenience tool.
- [x] Add `find_cells(query?, regex?, cellType?, includeOutputs=false)` to locate cells by source/output text.
- [x] Add validation for invalid cell IDs, invalid indices, and unsupported cell types.
- [x] Add tests for insert, update, move, delete, bulk replace, and metadata preservation.

## P0: Cell Execution And Interruption

- [x] Keep existing `run_code_cell(cellId)`.
- [x] Add `run_code_cells(cellIds, stopOnError=true, includeOutputs=true)`.
- [x] Add `run_cell_range(cellIndexStart, cellIndexEnd, stopOnError=true, includeOutputs=true)`.
- [x] Add `run_all_cells(stopOnError=true, includeOutputs=true)`.
- [x] Add `interrupt_execution(cellIds? = null)`: interrupt selected/running cells through Colab frontend API or UI fallback.
- [x] Add `cancel_queued_cells(cellIds? = null)` if Colab exposes queue state.
- [x] Add timeout support to execution wrappers: `timeoutSeconds`, with best-effort interrupt on timeout.
- [x] Return structured per-cell results: `cellId`, `startedAt`, `endedAt`, `durationSeconds`, `status`, `executionCount`, `outputs`, `error`.
- [x] Add tests for successful batch execution, stop-on-error, continue-on-error, timeout, and interrupt.

## P0: Cell Execution Status

- [x] Add `get_cell_status(cellIds? = null, includeOutputs=false)`.
- [x] Status fields: `cellId`, `index`, `cellType`, `state`, `busy`, `queued`, `executionCount`, `hasError`, `lastOutputText`, `outputCount`.
- [x] Use browser state where available: `busyCellIds`, execution queue, code execution model, visible DOM status.
- [x] Fall back to `get_cells(includeOutputs=true)` when browser state is unavailable.
- [x] Add `wait_for_cells(cellIds, targetStates, timeoutSeconds, pollIntervalSeconds=0.5)`.
- [x] Add tests/mocks for idle, queued, running, success, error, interrupted, and unknown.

## P0: Immediate Output Reading

- [x] Add `read_cell_outputs(cellIds, since? = null, maxBytes? = null)`.
- [x] Add `watch_cell_outputs(cellIds, pollIntervalSeconds=0.5, timeoutSeconds?)` for polling-based streaming.
- [x] Add browser-side visible output observer. `MutationObserver` streaming remains a later hardening item.
- [x] Normalize output chunks: stdout, stderr, display data, execute result, error traceback.
- [x] Include timestamps for observed output chunks.
- [x] Provide a reliable path for long experiments: `start_background_command` plus `tail_file` or `watch_file`.
- [x] Add tests for stream output, error output, rich display output, and large output truncation.

## P0: Environment Variables

- [x] Keep existing `set_env_vars(variables, persist=false, markerName='default', cellIndex?)`.
- [x] Keep existing `rerun_env_setup_cells(markerName?, includeOutputs=true)`.
- [x] Add `get_env_vars(names? = null, redactPatterns? = ['KEY', 'TOKEN', 'SECRET', 'PASSWORD'])`.
- [x] Add `unset_env_vars(names, persist=false, markerName='default')`.
- [x] Add `.env` upload/apply helper: `load_env_file(path, persist=false, markerName='default')`.
- [x] Redact sensitive values in text output while keeping structured metadata useful.
- [x] Add tests for set, get, unset, persist, rerun, and redaction.

## P0: Colab Terminal And Shell

- [x] Keep existing `run_shell_command(command, timeoutSeconds=600, cwd?)`.
- [x] Keep existing `start_background_command(command, name?, logPath?, cwd?)`.
- [x] Keep existing `check_background_command(name)`.
- [x] Keep existing `stop_background_command(name, signal=15)`.
- [x] Keep existing `tail_file(path, lines=80, maxBytes=20000)`.
- [x] Add `list_background_commands()`.
- [x] Add `watch_background_command(name, pollIntervalSeconds=1, timeoutSeconds?)`.
- [x] Route shell/background/log tools through Colab Terminal's `/colab/tty` websocket instead of temporary notebook cells so they still work while a training cell is running.
- [x] Add `open_terminal` browser tool that opens the Colab terminal pane.
- [x] Add terminal UI snapshot/control helpers for visible terminal text and sending command text if feasible.
- [x] Clearly separate non-interactive shell MCP from browser terminal UI; prefer MCP shell for automation.
- [x] Add tests for cwd, timeout, stdout/stderr, background registry, tailing, stop, and missing job.

## P0: Runtime File Upload And Download

- [x] Add `upload_file(path, contentBase64, overwrite=false, mode='binary', makeParents=true)`.
- [x] Add `download_file(path, maxBytes? = null, offset=0, encoding='base64')`.
- [x] Add `stat_file(path)`.
- [x] Add `list_files(path='.', recursive=false, maxEntries=1000)`.
- [x] Add `delete_file(path, recursive=false)`.
- [x] Add `make_directory(path, parents=true, existOk=true)`.
- [x] Add chunked upload/download for large files: `upload_file_chunk`, `download_file_chunk`, `complete_upload`.
- [x] Route runtime file tools through Colab file APIs: browser `kernelFiles.write` for upload, `/files` Range for download, and contents API for list/stat/delete.
- [x] Return hashes where useful: size, mtime, sha256 for complete files.
- [x] Prevent accidental destructive operations outside intended runtime workspace unless explicitly forced.
- [x] Add tests for text, binary, large/chunked files, overwrite=false, missing files, and non-ASCII paths.

## P0: GPU Utilization With Timestamps

- [x] Keep `check_gpu` on the Colab Terminal/nvidia-smi path so it does not consume a notebook cell slot.
- [x] Add MCP-native `set_runtime_accelerator(accelerator, apply=true)` for Colab runtime type changes.
- [x] Fold accelerator UI inspection into `check_runtime`.
- [x] Keep `resource_usage_snapshot(savePath='/content/colab_mcp_usage.jsonl')` on the Colab Terminal path.
- [x] Add `sample_gpu_usage(intervalSeconds=1.0, count=1, savePath='/content/colab_mcp_gpu.jsonl')` using Terminal/nvidia-smi.
- [x] Include `timestamp`, `isoTimestamp`, `gpuIndex`, `name`, `memoryTotalMiB`, `memoryUsedMiB`, `memoryFreeMiB`, `gpuUtilizationPercent`, `memoryUtilizationPercent`, `temperatureC`, `powerDrawW`.
- [x] Prefer lightweight `nvidia-smi` metrics for GPU sampling; avoid torch imports in monitor paths.
- [x] Add `start_gpu_monitor(name='gpu', intervalSeconds=1.0, savePath?)` as a lightweight Terminal/nvidia-smi background sampler.
- [x] Add `stop_gpu_monitor(name='gpu')`.
- [x] Add `read_gpu_monitor(name='gpu', lines=100)` to fetch JSONL samples.
- [x] Gracefully handle no GPU, missing `nvidia-smi`, and multiple GPUs.
- [x] Add tests using mocked `nvidia-smi` output.

## P1: Browser Extension Tools

- Dropped: browser userscript / `colab_ext.*` tools are not part of the default build or supported runtime path.

## P1: Local Browser Control

- [x] Import or rewrite Edge CDP helpers into this repo under `src/colab_mcp/browser_control` or `scripts/`.
- [x] Add `start_edge_debug`.
- [x] Add `list_tabs`.
- [x] Add `eval_tab`.
- [x] Add `click_text`.
- [x] Add `snapshot`.
- [x] Add `connect_colab_mcp_edge`.
- [x] Add `colab_runtime_ui` accelerator controls.
- [x] Promote accelerator controls into Python MCP tools so training workflows do not depend on `colabctl`.
- [x] Add `colabctl keepalive` to periodically focus/click the dedicated Colab page during long runs.
- [x] Use a persistent dedicated Edge profile (`~/.codex/edge-colab-mcp-profile`) so login state survives restarts.
- Deferred: try a headless dedicated Edge flow using the saved profile after the headed workflow is stable.
- [x] Integrate these helpers into `colabctl`.
- [x] Avoid relying on `G:\Surper_GCG` paths; this repo must be self-contained.

## P1: API Quality

- [x] Normalize all tool names and schemas.
- [x] Use consistent casing: MCP external schemas can keep Colab-style names, internal Python should use snake_case.
- [x] Return structured content for every tool.
- [x] Include `ok`, `status`, `error`, and `warnings` in structured results where applicable.
- [x] Add sane output truncation defaults with explicit `maxBytes`.
- [x] Add redaction for secrets in text output.
- [x] Add docs examples for every tool.
- [x] Add compatibility notes for Colab Free/Pro, GPU/no GPU, disconnected runtime, and browser not logged in.

## P1: Reliability

- [x] Reconnect after Colab page refresh.
- [x] Reconnect after runtime restart.
- [x] Detect stale WebSocket state.
- [x] Detect Colab disconnected runtime separately from MCP disconnected browser.
- [x] Detect and report account/login state.
- [x] Detect GPU runtime type and warn when no accelerator is active.
- [x] Add retry policy for transient Colab frontend errors.
- [x] Add operation audit log with timestamps and tool names.
- Resolved on 2026-05-04: full MCP-only ResCNN smoke was blocked before training because `set_runtime_accelerator("T4 GPU")` selected T4 in the browser, but terminal-backed tools still could not see `kernel.runtime`. Root fix: add a dedicated `connect_runtime(waitSeconds)` MCP tool that closes/avoids local MCP connect UI, clicks the Colab runtime toolbar, and waits for a real runtime plus terminal socket before `check_gpu`, file APIs, or background commands run.

## P2: Packaging And Release

- [x] Keep package installable with `uv run colab-mcp`.
- [x] Add console script `colabctl`.
- [x] Add versioning policy for fork builds.
- [x] Add `CHANGELOG.md`.
- [x] Add `docs/USAGE.md`.
- [x] Add `docs/TOOLS.md`.
- [x] Add `docs/TROUBLESHOOTING.md`.
- [x] Add examples for common workflows: setup, run experiment, watch logs, download results, monitor GPU.
- Release action: make the initial git commit after the baseline TODO is accepted.
