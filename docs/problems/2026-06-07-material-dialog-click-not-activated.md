# Material Dialog Click Not Activated

- Date: 2026-06-07
- Area: Live shell-mode Colab MCP connection

## Exact Error

The shell-mode bridge remained at:

```text
Connecting Colab MCP browser session...
```

CDP inspection showed the Colab page had the correct token and port, the local MCP server was listening on both `127.0.0.1` and `::1`, but the approval dialog remained open and the browser websocket stayed in `CONNECTING` state:

```json
{
  "serviceConnected": true,
  "ws": {
    "readyState": 0,
    "url": "ws://localhost:44161/?access_token=_I-dd4mmpJFUMEuCfFHcKg"
  },
  "bodyTail": "... Terminal\\nCancelConnect"
}
```

The visible interactive elements included:

```json
[
  {"tag": "DIV", "role": "dialog", "text": "Connect to a local Colab MCP server ..."},
  {"tag": "MD-TEXT-BUTTON", "text": "Cancel Cancel"},
  {"tag": "MD-TEXT-BUTTON", "text": "Connect Connect"}
]
```

## Reproduction Steps

1. Start the shell-mode bridge with the copied signed Chrome profile and CDP port `9463`.
2. Wait for the log to remain at `Connecting Colab MCP browser session...`.
3. Inspect the Colab page through CDP and observe the approval dialog plus a `CONNECTING` websocket.
4. Check local listeners and observe the requested MCP port bound on both IPv4 and IPv6 loopback.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser CDP port: `9463`
- Browser account: `canbehumanagain@gmail.com`
- Local terminal mode: `--terminal-command shell`
- Live MCP websocket port observed: `44161`
- Local listener state: `127.0.0.1:44161` and `[::1]:44161`

## First Hypothesis

The CDP helper finds the Material `md-text-button` host for `Connect`, but synthetic DOM mouse events on the host do not activate Colab's Material dialog. The click path should prefer the real inner button or use CDP mouse input at the element center.
