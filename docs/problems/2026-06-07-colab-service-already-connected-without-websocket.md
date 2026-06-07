# Colab Service Already Connected Without Websocket

- Date: 2026-06-07
- Area: Colab MCP browser attach

## Exact Error

After moving browser attach work off the FastMCP event loop, the live bridge still stayed at:

```text
Connecting Colab MCP browser session...
```

CDP inspection showed Colab's frontend service had no open websocket and reported disconnected, but the connect automation captured a Colab exception:

```json
{
  "serviceConnected": false,
  "ws": null,
  "automation": {
    "done": true,
    "resolved": false,
    "error": "MCP server already connected",
    "token": "8F2mIbvdduGhrogRSZUEqw",
    "port": "33373"
  }
}
```

The local websocket server log simultaneously showed repeated aborted handshakes:

```text
websockets.exceptions.InvalidMessage: did not receive a valid HTTP request
```

## Reproduction Steps

1. Start the shell-mode bridge with threaded browser attach and CDP mouse-click dialog handling.
2. Wait for the browser URL/session storage to contain the fresh token and port.
3. Inspect `window.__colabMcpConnectAutomation` and `localColabMcpService`.
4. Observe `MCP server already connected` with no frontend websocket object.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser CDP port: `9463`
- Browser account: `canbehumanagain@gmail.com`
- Terminal mode: `--terminal-command shell`
- MCP websocket port observed: `33373`

## First Hypothesis

Colab's `localColabMcpService` can retain an internal stale server/connection flag across token changes even after `disconnect()`. The attach helper should recover by reloading or replacing the Colab tab when this inconsistent state appears.
