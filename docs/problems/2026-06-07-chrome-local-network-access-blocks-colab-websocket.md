# Chrome Local Network Access Blocks Colab Websocket

- Date: 2026-06-07
- Area: Controlled Chrome browser attach

## Exact Error

The live shell bridge stayed at:

```text
Connecting Colab MCP browser session...
```

After the Colab approval dialog closed, CDP showed no transport:

```json
{
  "serviceConnected": false,
  "ws": null,
  "dialogOpen": false
}
```

A direct browser-created websocket from the Colab HTTPS page to the local MCP listener failed for every loopback URL:

```json
[
  {"url": "ws://localhost:41205/?access_token=...", "event": "error", "readyState": 3},
  {"url": "ws://127.0.0.1:41205/?access_token=...", "event": "error", "readyState": 3},
  {"url": "ws://[::1]:41205/?access_token=...", "event": "error", "readyState": 3}
]
```

The server logged aborted handshakes:

```text
websockets.exceptions.InvalidMessage: did not receive a valid HTTP request
```

Local Chrome 148 exposes Local Network Access websocket feature gates:

```text
LocalNetworkAccessChecks
LocalNetworkAccessChecksWebSockets
LocalNetworkAccessRestrictionsTemporaryOptOut
```

## Reproduction Steps

1. Start the shell-mode bridge in the controlled Chrome profile.
2. Let the helper close the Colab local MCP approval dialog.
3. From the Colab page, create `new WebSocket("ws://localhost:<mcp_port>/?access_token=<token>")`.
4. Observe immediate browser websocket errors and empty aborted handshakes on the local server.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: Google Chrome `148.0.7778.215`
- Controlled Chrome CDP port: `9463`
- MCP websocket port observed: `41205`
- Browser account: `canbehumanagain@gmail.com`

## First Hypothesis

Chrome 148's Local Network Access websocket checks are blocking or aborting loopback websocket handshakes from the HTTPS Colab page before a valid HTTP websocket request reaches the local MCP server.
