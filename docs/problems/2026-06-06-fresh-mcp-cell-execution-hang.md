# Fresh MCP cell execution hang

- Timestamp: 2026-06-06T14:10:18+05:30
- Problem slug: fresh-mcp-cell-execution-hang

## Exact Error

A fresh client-managed MCP session connected to a new Colab scratch URL, but a simple cell execution probe did not return after the connection succeeded.

Observed probe output:

```text
scratch https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>
connected False elapsed 3
connected False elapsed 6
connected False elapsed 9
connected False elapsed 12
connected False elapsed 15
connected False elapsed 18
connected False elapsed 21
connected False elapsed 24
connected False elapsed 27
connected False elapsed 30
connected False elapsed 33
connected False elapsed 36
connected False elapsed 39
connected False elapsed 42
connected False elapsed 45
connected False elapsed 48
connected False elapsed 51
connected True elapsed 54
```

After `connected True elapsed 54`, the probe did not return output from:

```python
print('fresh-mcp-probe-ok-20260606')
```

## Reproduction Steps

1. Launch a fresh FastMCP client-managed `uv run colab-mcp` server.
2. Open the returned scratch URL in `google-chrome-stable --new-window`.
3. Wait for `get_connection_info.connected` to become `true`.
4. Add a code cell with `print('fresh-mcp-probe-ok-20260606')`.
5. Call `run_code_cell`.
6. Observe that the call does not return after the MCP browser connection succeeds.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser profile: existing Chrome `Default`
- Prior failure in same runtime: `docs/problems/2026-06-06-opencode-install-script-preview-hang.md`
- Existing tmux bridge: `colab-cell-terminal`, stuck after the install-script preview command
- CDP state: unavailable on `9333`, `9222`, and `9223`

## First Hypothesis

The earlier hanging cell execution is still occupying the Colab runtime's single notebook execution slot. Fresh notebook-cell execution is therefore queued or blocked even though the MCP browser frontend connection itself succeeds.
