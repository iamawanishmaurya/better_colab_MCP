# Chrome Local Network Access Websocket Flags

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-chrome-local-network-access-blocks-colab-websocket.md](../problems/2026-06-07-chrome-local-network-access-blocks-colab-websocket.md)

## What Failed

The Colab page could not establish a browser websocket to the local MCP server. Direct `new WebSocket(...)` tests from the Colab page failed for `localhost`, `127.0.0.1`, and `[::1]`, while the local server logged empty aborted handshakes.

## Alternatives Considered

1. Keep retrying Colab dialog automation. Rejected because direct browser-created websockets failed independently of the Colab service.
2. Use a TLS `wss://localhost` server. Higher implementation cost and certificate trust setup, not needed if Chrome's local-network checks can be disabled for the controlled profile.
3. Bind only IPv4 or only IPv6. Rejected because both loopback families were already tested and failed from the browser.
4. Restart the controlled Chrome with local-network websocket checks disabled. Chosen because the local Chrome binary exposes `LocalNetworkAccessChecks` and `LocalNetworkAccessChecksWebSockets`, and the controlled profile is dedicated to Colab MCP automation.
5. Ask the user to grant Chrome's local network permission manually. Rejected for the automated-connect workflow.

## What Worked

The controlled Chrome launch command now adds:

```text
--disable-features=LocalNetworkAccessChecks,LocalNetworkAccessChecksWebSockets,BlockInsecurePrivateNetworkRequests
```

The behavior can be disabled with:

```bash
COLAB_MCP_BROWSER_DISABLE_LOCAL_NETWORK_CHECKS=0
```

## Why It Worked

The failure happened before a valid websocket HTTP request reached the local MCP server. Disabling Chrome's local-network websocket checks for the controlled Colab MCP profile allows Colab's HTTPS page to reach the loopback websocket server.

## Commands Run

```bash
strings /opt/google/chrome/chrome | rg -i 'LocalNetworkAccess|BlockInsecurePrivateNetwork|PrivateNetworkAccess|NetworkServiceSandbox'
google-chrome-stable --version
uv run pytest tests/session_test.py::TestControlledEdgeLaunch tests/session_test.py::TestCheckSessionProxyToolFn tests/session_test.py::TestConnectColabTab tests/websocket_server_test.py::test_successful_ipv6_loopback_connection tests/opencode_setup_cell_test.py -q
```
