# Tools

This fork exposes the upstream Colab frontend tools plus additional runtime and browser helpers.

## Notebook And Cells

- `add_code_cell`
- `add_text_cell`
- `delete_cell`
- `get_cells`
- `move_cell`
- `run_code_cell`
- `update_cell`
- `upload_notebook`
- `download_notebook`
- `import_notebook`
- `export_notebook`
- `replace_cells`
- `patch_cell`
- `get_cell`
- `find_cells`
- `run_code_cells`
- `run_cell_range`
- `run_all_cells`
- `get_cell_status`
- `wait_for_cells`
- `read_cell_outputs`
- `watch_cell_outputs`

Example:

```text
get_cells(includeOutputs=false)
run_code_cells(cellIds=["cell-a", "cell-b"], stopOnError=true, timeoutSeconds=60)
get_cell_status(cellIds=["cell-a", "cell-b"], includeOutputs=true)
read_cell_outputs(cellIds=["cell-a"], normalize=true)
download_notebook(path="C:\\temp\\scratch.ipynb", includeOutputs=true)
```

## Environment And Runtime

- `set_env_vars`
- `get_env_vars`
- `unset_env_vars`
- `load_env_file`
- `rerun_env_setup_cells`
- `check_runtime`
- `connect_runtime`
- `restart_runtime`
- `shutdown_runtime`
- `set_runtime_accelerator`

Example:

```text
set_env_vars(variables={"HF_HOME": "/content/hf_cache"}, persist=true)
get_env_vars(names=["HF_HOME", "HF_TOKEN"])
load_env_file(path="C:\\project\\.env", persist=false)
check_runtime()
set_runtime_accelerator(accelerator="T4 GPU", apply=true)
connect_runtime(waitSeconds=180)
```

`set_runtime_accelerator` uses the controlled browser/CDP path from the MCP
server itself. Applying a change can restart or disconnect the runtime; call
`open_colab_browser_connection` and `connect_runtime` again before running
shell, GPU, or file tools.

## Shell And Background Jobs

- `run_shell_command`
- `start_background_command`
- `check_background_command`
- `list_background_commands`
- `watch_background_command`
- `tail_file`
- `stop_background_command`

These tools use Colab Terminal's `/colab/tty` websocket directly instead of
temporary notebook cells. The browser is used only to discover the active
runtime terminal endpoint and proxy token, so shell and background job control
can continue while a training cell occupies Colab's single cell execution slot.

Example:

```text
run_shell_command(command="python --version", timeoutSeconds=30)
start_background_command(name="train", command="python train.py", logPath="/content/train.log")
watch_background_command(name="train", lines=100)
stop_background_command(name="train")
```

Background commands write stdout and stderr to the log file and maintain a status JSON with `running`, `returncode`, `startedAt`, `finishedAt`, and `durationSeconds` when available.

## Runtime Files

- `upload_file`
- `upload_local_file`
- `download_file`
- `download_file_to_local`
- `upload_file_chunk`
- `complete_upload`
- `download_file_chunk`
- `stat_file`
- `list_files`
- `make_directory`
- `delete_file`

These tools run through the same Colab Terminal backend used by shell commands
instead of temporary notebook cells. Results are written to a small runtime
result file and read back through the runtime contents API, so file management
does not consume the notebook cell execution slot.

Example:

```text
make_directory(path="/content/data")
upload_local_file(localPath="<path-to-input.txt>", path="/content/data/input.txt", overwrite=true)
stat_file(path="/content/data/input.txt")
download_file_to_local(path="/content/data/input.txt", localPath="<path-to-output.txt>", overwrite=true)
delete_file(path="/content/data/input.txt")
```

Use `upload_file` and `download_file` when the caller needs base64 payloads.
For normal local-file workflows, prefer `upload_local_file` and
`download_file_to_local`.

## GPU

- `check_gpu`
- `resource_usage_snapshot`
- `sample_gpu_usage`
- `start_gpu_monitor`
- `stop_gpu_monitor`
- `read_gpu_monitor`

Example:

```text
check_gpu()
sample_gpu_usage(intervalSeconds=1, count=3)
start_gpu_monitor(name="gpu", intervalSeconds=1)
read_gpu_monitor(name="gpu", lines=20)
stop_gpu_monitor(name="gpu")
```

Use `set_runtime_accelerator(accelerator="T4 GPU")` before GPU work when a
specific accelerator is required.

## Local CLI

`colabctl` is a local browser/control helper:

By default it uses CDP port `9333` and a dedicated browser profile so it does
not navigate your normal browser tabs. Set `COLAB_MCP_BROWSER_COMMAND`,
`COLAB_MCP_BROWSER_USER_DATA_DIR`, and `COLAB_MCP_BROWSER_PROFILE` to reuse an
existing authenticated Chrome profile.

- `colabctl status`
- `colabctl connect`
- `colabctl eval`
- `colabctl smoke-browser`
- `colabctl smoke-mcp`
- `colabctl list-tabs`
- `colabctl snapshot`
- `colabctl click-text`
- `colabctl keepalive`
- `colabctl set-accelerator`

Example:

```powershell
uv run colabctl status
uv run colabctl connect
uv run colabctl smoke-browser
uv run colabctl keepalive
uv run colabctl set-accelerator --accelerator GPU
```

`colabctl set-accelerator` is kept for diagnostics. Normal automation should
prefer the MCP tool `set_runtime_accelerator`.
