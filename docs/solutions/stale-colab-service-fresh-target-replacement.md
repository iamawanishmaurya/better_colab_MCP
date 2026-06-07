# Stale Colab Service Fresh Target Replacement

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-colab-service-already-connected-without-websocket.md](../problems/2026-06-07-colab-service-already-connected-without-websocket.md)

## What Failed

A full `about:blank` then target-url navigation reset did not clear Colab's stale local MCP service state. The same tab continued reporting:

```text
MCP server already connected
```

while `localColabMcpService.isConnected()` was false and no inner websocket object existed.

## Alternatives Considered

1. Retry the same full reload again. Rejected because the same error repeated after one reset, and another reload would be the same fix.
2. Click the visible approval dialog again. Rejected because the service was already throwing before a websocket object existed, so click-only recovery would not clear the stale service singleton.
3. Restart the whole Chrome profile. This would likely clear the page state, but it is slower, disrupts the visible browser, and can lose useful signed-profile continuity.
4. Poke private Colab service fields from JavaScript. Rejected because the frontend is minified and private field names can change.
5. Close the stale Colab page target and create a fresh page target in the same signed Chrome profile. Chosen because it resets page JavaScript state while keeping the authenticated browser/profile and uses documented CDP target/page primitives.

## What Worked

Implemented a fresh-target fallback:

- `_connect_colab_tab()` now returns `False` when the same stale `MCP server already connected` state persists after the one-time tab reset.
- `_navigate_controlled_edge()` closes the stale target, opens a fresh Colab scratchpad target, reapplies cookie-file auth if configured, and reruns `_connect_colab_tab()` on the fresh target.

## Why It Worked

The stale state is held in the page's JavaScript runtime, not the Chrome profile. Replacing the page target clears the runtime singleton without throwing away the signed-in browser profile.

## Commands Run

```bash
uv run python - <<'PY'
# CDP inspection of localColabMcpService, automation state, and websocket state.
PY
ss -tanp | rg '43469|271651|9463|chrome'
uv run pytest tests/session_test.py::TestCheckSessionProxyToolFn tests/session_test.py::TestConnectColabTab tests/websocket_server_test.py::test_successful_ipv6_loopback_connection tests/opencode_setup_cell_test.py -q
```
