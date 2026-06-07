# Signed CDP MCP Transport Reconnect

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-signed-cdp-profile-mcp-transport-not-attached.md](../problems/2026-06-07-signed-cdp-profile-mcp-transport-not-attached.md)

## What Failed

The signed copied profile opened in a CDP-controlled Colab tab, but the launcher timed out with:

```text
RuntimeError: Colab MCP did not connect: opened={'result': False}
```

CDP inspection showed Colab's wrapper connection state could be stale: `localColabMcpService.isConnected()` was not enough evidence that the inner frontend MCP server transport was attached.

## What Worked

The attach helper now checks the inner frontend MCP server state before deciding whether to skip `localColabMcpService.connect()`. If the wrapper appears connected but the inner server is disconnected, it disconnects stale state, refreshes the token/port, calls `connect()`, and requires `serverConnected=true` before returning success.

## Why It Worked

A temporary websocket probe proved that Colab's frontend can connect correctly when `localColabMcpService.connect()` is invoked. It connects to:

```text
/?access_token=<redacted>
```

with origin `https://colab.research.google.com` and subprotocol `mcp`. The failure was therefore stale frontend state causing the helper to skip the real connect call, not a login or token transport problem.

## Commands Run

```bash
uv run python - <<'PY'
# Temporary websocket probe on the failed proxy port, then CDP invocation of localColabMcpService.connect().
PY
uv run pytest tests/session_test.py -q
uv run python - <<'PY'
# Three-cycle live MCP attach validation using CDP port 9463 and copied signed Default profile.
PY
uv run python - <<'PY'
# Runtime validation: open_colab_browser_connection, connect_runtime, check_runtime.
PY
```

## Evidence

```text
53 passed in 3.64s

Cycle 1: connected=true, innerTransport=MZb, port=42017
Cycle 2: connected=true, innerTransport=MZb, port=38001
Cycle 3: connected=true, innerTransport=MZb, port=33053

check_runtime: status=ok, python=3.12.13, cwd=/content, executionBackend=colab-terminal
```
