# Reconnect proxy tests failing

- Timestamp: 2026-06-06T14:50:08+05:30
- Problem slug: reconnect-proxy-tests-failing

## Exact Error

Focused proxy-client tests failed after adding the reconnect loop:

```text
FAILED tests/session_test.py::TestColabProxyClient::test_is_connected
assert False is True

FAILED tests/session_test.py::TestColabProxyClient::test_client_factory_connection_live
AssertionError: assert <fastmcp.client.client.Client object ...> is <Mock ...>

FAILED tests/session_test.py::TestColabProxyClient::test_start_proxy_client_reconnects_after_disconnect
AssertionError: assert <AsyncMock ...> is <AsyncMock ...>

3 failed, 3 passed in 5.06s
```

`uv run ruff check .` and `uv run python -m compileall -f src scripts` passed.

## Reproduction Steps

1. Add reconnect-ready state to `ColabProxyClient`.
2. Run:

   ```sh
   uv run pytest tests/session_test.py::TestColabProxyClient -q
   ```

3. Observe the three failures above.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Python: 3.13.13 through `uv`
- Test target: `tests/session_test.py::TestColabProxyClient`

## First Hypothesis

Two older tests still model connectivity as `connection_live + proxy_mcp_client`, but the implementation now also requires `_client_ready`. The reconnect test also uses `AsyncMock` as an async context manager in a way that returns a generated child mock instead of the intended client instance.

## Follow-Up Failure

Timestamp: 2026-06-06T14:51:23+05:30

After replacing `AsyncMock` with an explicit async context stub, one focused test still failed:

```text
FAILED tests/session_test.py::TestColabProxyClient::test_start_proxy_client_reconnects_after_disconnect
assert <AsyncClientContext object ...> is <AsyncClientContext object ...>
```

Follow-up hypothesis: patching `colab_mcp.session.Client` also affects `ColabProxyClient.__init__`, where `stubbed_mcp_client = Client(FastMCP())` consumes the first mock side-effect before the reconnect loop creates the proxy client.
