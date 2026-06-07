# Fresh Target Fallback Test Fixture Scope

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-fresh-target-fallback-test-returned-false.md](../problems/2026-06-07-fresh-target-fallback-test-returned-false.md)

## What Failed

The new fresh-target fallback unit test called `_navigate_controlled_edge()`, but the module's autouse fixture had already replaced that function with a mock returning `False`.

## What Worked

The autouse fixture now skips patching `_navigate_controlled_edge()` for `test_navigate_controlled_edge_replaces_stale_colab_target`.

## Why It Worked

That test is specifically validating `_navigate_controlled_edge()` itself. Letting the real function run while still mocking its CDP dependencies exercises the fallback behavior without opening a real browser.

## Commands Run

```bash
uv run pytest tests/session_test.py::TestControlledEdgeLaunch tests/session_test.py::TestCheckSessionProxyToolFn tests/session_test.py::TestConnectColabTab tests/websocket_server_test.py::test_successful_ipv6_loopback_connection tests/opencode_setup_cell_test.py -q
```
