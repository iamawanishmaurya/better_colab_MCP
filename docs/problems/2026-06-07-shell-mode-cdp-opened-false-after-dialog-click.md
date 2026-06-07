# Shell Mode CDP Opened False After Dialog Click

- Date: 2026-06-07
- Area: Live shell-mode Colab MCP connection

## Exact Error

After the visible Colab MCP dialog was closed through CDP mouse input, the shell-mode bridge still timed out and exited:

```text
RuntimeError: Colab MCP did not connect: opened={'result': False} info={'host': '127.0.0.1', 'port': 44161, 'token': '_I-dd4mmpJFUMEuCfFHcKg', 'scratchUrl': 'https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=_I-dd4mmpJFUMEuCfFHcKg&mcpProxyPort=44161', 'pid': 215375, 'connected': False, ...}
```

Immediately before the timeout, CDP showed:

```json
{
  "serviceConnected": true,
  "ws": {
    "readyState": 0,
    "url": "ws://localhost:44161/?access_token=_I-dd4mmpJFUMEuCfFHcKg"
  },
  "dialogOpen": false
}
```

## Reproduction Steps

1. Start the shell-mode bridge with the copied signed Chrome profile and CDP port `9463`.
2. Wait until the page shows the local MCP approval dialog.
3. Click the visible `Connect` button through CDP mouse coordinates.
4. Continue polling the bridge log until the bridge exits with `opened={'result': False}`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser CDP port: `9463`
- Browser account: `canbehumanagain@gmail.com`
- Local terminal mode: `--terminal-command shell`
- MCP websocket port observed: `44161`
- Local terminal port requested: `8768`

## First Hypothesis

The dialog click must be coordinated inside the active `localColabMcpService.connect()` window. Closing the dialog from a separate diagnostic after the helper is already looping can leave Colab's frontend in a stale `isConnected()` state with a non-open websocket.
