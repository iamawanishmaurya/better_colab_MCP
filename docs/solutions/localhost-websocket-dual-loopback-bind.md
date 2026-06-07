# Localhost Websocket Dual Loopback Bind

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-localhost-websocket-ipv6-not-bound.md](../problems/2026-06-07-localhost-websocket-ipv6-not-bound.md)

## What Failed

The Colab frontend opened `ws://localhost:<port>`, but the local MCP websocket server only listened on `127.0.0.1:<port>`. In the failing browser state, the frontend websocket stayed at `readyState: 0`.

## What Worked

After the existing IPv4 bind chooses a random port, the server now attempts to bind an additional IPv6 loopback listener on `::1` using the same port. If IPv6 loopback is unavailable, the server logs the bind failure and continues with IPv4.

## Why It Worked

Chrome's `localhost` resolution may use either IPv4 or IPv6. Binding both loopback families makes Colab's fixed `ws://localhost:<port>` URL reliable without exposing the server beyond localhost.

## Commands Run

```bash
uv run python - <<'PY'
# Verified that binding 127.0.0.1:0 and then ::1:<same-port> works on this host.
PY
uv run pytest tests/websocket_server_test.py::test_successful_ipv6_loopback_connection -q
```
