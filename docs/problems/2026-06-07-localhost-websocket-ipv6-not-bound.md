# Localhost Websocket IPv6 Not Bound

- Date: 2026-06-07
- Area: Colab MCP websocket transport

## Exact Error

The shell-mode bridge stayed at:

```text
Connecting Colab MCP browser session...
```

CDP inspection showed Colab had created a websocket transport, but the browser socket was still connecting:

```json
{
  "readyState": 0,
  "url": "ws://localhost:37101/?access_token=<redacted>",
  "protocol": "",
  "bufferedAmount": 0
}
```

The local server was listening only on IPv4:

```text
LISTEN 0 100 127.0.0.1:37101 0.0.0.0:* users:(("colab-mcp",pid=179374,fd=7))
```

## Reproduction Steps

1. Start a Colab MCP server that binds only `127.0.0.1`.
2. Let Colab's frontend create its local MCP websocket at `ws://localhost:<port>`.
3. Inspect the browser transport through CDP:

   ```javascript
   window.colab.global.notebook.localColabMcpService.colabMcpServer.server._transport.ws.readyState
   ```

4. Observe `readyState: 0` with no established TCP connection.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: Chrome signed copied profile on CDP `9463`
- MCP websocket URL from Colab: `ws://localhost:37101/?access_token=<redacted>`
- MCP server listener before fix: `127.0.0.1:37101`

## First Hypothesis

Chrome can resolve `localhost` to IPv6 `::1`, while the MCP websocket server only listened on IPv4 `127.0.0.1`. The server should also bind IPv6 loopback on the same selected port.
