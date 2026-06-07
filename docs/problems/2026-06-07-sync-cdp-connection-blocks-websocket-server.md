# Sync CDP Connection Blocks Websocket Server

- Date: 2026-06-07
- Area: Colab MCP browser attach

## Exact Error

The shell-mode bridge stayed at:

```text
Connecting Colab MCP browser session...
```

After the CDP mouse-click automation accepted the Colab dialog, CDP showed no visible approval dialog and an active Colab connect automation state, but the frontend websocket stayed in `CONNECTING`:

```json
{
  "serviceConnected": true,
  "ws": {
    "readyState": 0,
    "url": "ws://localhost:35767/?access_token=cDLJqwj6NQkSp-qPKRgcaw"
  },
  "automation": {
    "done": true,
    "resolved": true,
    "error": null
  }
}
```

The local socket table showed Chrome reaching the loopback listener while the MCP tool call was still running:

```text
ESTAB [::1]:58512 [::1]:35767 users:(("chrome",...))
ESTAB [::1]:35767 [::1]:58512
```

## Reproduction Steps

1. Start the shell-mode bridge with CDP auto-click enabled.
2. Wait until the Colab dialog disappears.
3. Inspect CDP state and socket state while the bridge log still shows `Connecting Colab MCP browser session...`.
4. Observe that browser TCP connections reach the local websocket listener, but the MCP tool does not complete.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser CDP port: `9463`
- Browser account: `canbehumanagain@gmail.com`
- Terminal mode: `--terminal-command shell`
- MCP websocket port observed: `35767`

## First Hypothesis

`_connect_colab_tab()` is synchronous and runs inside the FastMCP tool call. While it waits for the browser websocket to become `OPEN`, it blocks the same asyncio event loop that needs to accept and process that websocket connection.
