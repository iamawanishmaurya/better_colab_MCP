# Examples

## Setup

```powershell
uv sync --dev
uv run pytest -q
uv run colab-mcp
```

In another shell:

```powershell
uv run colabctl connect
uv run colabctl smoke-browser
```

## Run An Experiment

```text
open_colab_browser_connection()
set_runtime_accelerator(accelerator="T4 GPU", apply=true)
open_colab_browser_connection()
connect_runtime(waitSeconds=180)
check_gpu()
set_env_vars(variables={"HF_HOME": "/content/hf_cache"}, persist=true)
start_background_command(
  name="paper-run",
  command="python run_paper.py",
  cwd="/content/project",
  logPath="/content/results/paper-run.log"
)
watch_background_command(name="paper-run", lines=120)
```

## Download Results

```text
stat_file(path="/content/results/paper-run.log")
download_file_to_local(path="/content/results/paper-run.log", localPath="<path-to-paper-run.log>", overwrite=true)
```

## Monitor GPU

```text
start_gpu_monitor(name="gpu", intervalSeconds=1, savePath="/content/results/gpu.jsonl")
read_gpu_monitor(name="gpu", path="/content/results/gpu.jsonl", lines=50)
stop_gpu_monitor(name="gpu")
```

## Notebook Cell Batch

```text
get_cells(includeOutputs=false)
run_code_cells(cellIds=["cell-a", "cell-b"], stopOnError=true)
get_cell_status(cellIds=["cell-a", "cell-b"], includeOutputs=true)
read_cell_outputs(cellIds=["cell-a", "cell-b"])
```
