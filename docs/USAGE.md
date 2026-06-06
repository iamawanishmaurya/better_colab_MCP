# Usage

## Start The MCP Server

```powershell
uv sync --dev
uv run colab-mcp-test
```

```powershell
uv run colab-mcp
```

In an MCP client, point the server at this repository:

```json
{
  "mcpServers": {
    "colab-mcp": {
      "command": "uv",
      "args": ["run", "colab-mcp"],
      "cwd": "<path-to-colab_mcp>",
      "timeout": 30000
    }
  }
}
```

Replace `<path-to-colab_mcp>` with the absolute path to your local checkout.

## Connect A Browser

`colabctl` and `open_colab_browser_connection` use a controlled browser with
CDP port `9333`. By default the project keeps automation in a dedicated Edge
profile, but this fork can target an existing Chrome profile when you want to
reuse an authenticated session.

Recommended local Chrome profile for this workstation:

```powershell
$env:COLAB_MCP_BROWSER_COMMAND="google-chrome-stable"
$env:COLAB_MCP_BROWSER_USER_DATA_DIR="/home/astra/.config/google-chrome"
$env:COLAB_MCP_BROWSER_PROFILE="Default"
$env:COLAB_MCP_CONNECTION_TIMEOUT="180"
```

```powershell
uv run colabctl status
uv run colabctl connect
uv run colabctl smoke-browser
uv run colabctl smoke-mcp
```

The MCP tool `open_colab_browser_connection` can also start the controlled
browser directly. `colabctl connect` is primarily a diagnostic and manual repair
command.

If the dedicated browser is not logged in, these commands return
`loginRequired: true` with a prompt that the AI/client should show to the user.
Log into Google/Colab in the controlled browser window opened by `colabctl`, then rerun the
command.

Run browser smoke as part of the local test command when browser CDP and Colab are available:

```powershell
uv run colab-mcp-test --browser
```

Use `--allow-ambiguous` only when you intentionally have multiple local Colab MCP servers running:

```powershell
uv run colabctl connect --allow-ambiguous
```

If you intentionally want to attach to a different already-debuggable browser,
pass its port explicitly:

```powershell
uv run colabctl --port 9222 status
uv run colabctl --port 9222 connect
```

## Common Workflows

Run a shell command in Colab through MCP:

```text
run_shell_command(command="python --version")
```

Shell/background commands run through Colab Terminal's `/colab/tty` websocket,
not temporary notebook cells. The browser is only used to discover the active
runtime endpoint and proxy token, so these commands can still return results
while a long-running training cell is occupying the notebook execution slot.

Start a long experiment:

```text
start_background_command(
  name="experiment",
  command="python train.py",
  logPath="/content/experiment.log",
  cwd="/content/project"
)
```

Watch logs:

```text
watch_background_command(name="experiment", lines=100)
tail_file(path="/content/experiment.log", lines=100)
```

Upload/download runtime files:

```text
upload_local_file(localPath="<path-to-input.txt>", path="/content/input.txt", overwrite=true)
download_file_to_local(path="/content/output.txt", localPath="<path-to-output.txt>", overwrite=true)
```

Runtime file tools use the Colab Terminal backend and runtime contents API, not
temporary notebook cells, so they remain available while a notebook cell is
busy.

Monitor GPU:

```text
sample_gpu_usage(intervalSeconds=1, count=5)
start_gpu_monitor(name="gpu", intervalSeconds=1)
read_gpu_monitor(lines=100)
stop_gpu_monitor(name="gpu")
```

Switch Colab to a GPU runtime through MCP:

```text
set_runtime_accelerator(accelerator="T4 GPU", apply=true)
open_colab_browser_connection()
connect_runtime(waitSeconds=180)
check_gpu()
```

The same operation is also available from the local diagnostic CLI:

```powershell
uv run colabctl set-accelerator --accelerator GPU
uv run colabctl connect
```

Changing accelerators restarts or disconnects the runtime, so reconnect the
browser MCP and then call `connect_runtime` before running GPU checks.

Keep the Colab page active during long runs:

```powershell
uv run colabctl keepalive --interval 300 --forever
```

For a single manual keepalive pulse:

```powershell
uv run colabctl keepalive
```
