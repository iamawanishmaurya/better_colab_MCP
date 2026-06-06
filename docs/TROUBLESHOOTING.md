# Troubleshooting

## Browser Is Open But MCP Is Not Connected

Run:

```powershell
uv run colabctl status
uv run colabctl connect
```

`colabctl` defaults to CDP port `9333`. If a Colab page appears in the wrong
browser/profile, check `get_connection_info().browser`, `COLAB_MCP_BROWSER_COMMAND`,
`COLAB_MCP_BROWSER_USER_DATA_DIR`, `COLAB_MCP_BROWSER_PROFILE`, and whether you
explicitly passed `--port 9222` or started another browser manually with remote
debugging.

The active Colab-side state is `sessionStorage.mcp_proxy_token` and `sessionStorage.mcp_proxy_port`. The URL hash can become stale when multiple servers have run.

## Login Is Required

When the dedicated MCP browser is not logged into Colab, `colabctl status`,
`colabctl connect`, and smoke checks return machine-readable fields such as:

```json
{
  "loginRequired": true,
  "promptForAi": "Colab is not logged in in the controlled MCP browser. Ask the user to log into Google/Colab in the browser window opened by colabctl, then rerun the command."
}
```

In that case, tell the user to log into Google/Colab in the controlled browser
window opened by `colabctl`, then rerun the command.

## Multiple Servers Are Running

`colabctl connect` refuses ambiguous local state by default. Stop stale `colab-mcp` processes, or explicitly run:

```powershell
uv run colabctl connect --allow-ambiguous
```

## Colab Runtime Is Disconnected

Browser MCP connection and Python runtime connection are separate. `colabctl status` may show browser local MCP available while the runtime is disconnected. Use Colab UI or `check_runtime` to confirm runtime state.

## GPU Is Missing

`check_gpu` and `sample_gpu_usage` handle missing `nvidia-smi`. If no accelerator is selected, use the MCP runtime accelerator tool:

```text
set_runtime_accelerator(accelerator="T4 GPU", apply=true)
open_colab_browser_connection()
connect_runtime(waitSeconds=180)
check_gpu()
```

Changing accelerators restarts the runtime.

## File Upload Is Large

Use chunked APIs:

```text
upload_file_chunk(uploadId="run1", path="/content/big.bin", chunkBase64="...", chunkIndex=0, overwrite=true)
upload_file_chunk(uploadId="run1", path="/content/big.bin", chunkBase64="...", chunkIndex=1)
complete_upload(uploadId="run1", path="/content/big.bin", overwrite=true)
```

## Browser UI Text Does Not Match

Colab UI text depends on locale. Prefer MCP runtime tools for automation; browser UI control in this fork is limited to the Python/CDP paths.
