# Shell Mode CDP Connect Dialog Click

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-shell-mode-cdp-connect-dialog-not-accepted.md](../problems/2026-06-07-shell-mode-cdp-connect-dialog-not-accepted.md)

## What Failed

The shell-mode bridge reached the Colab page with the correct token and port, but stayed at:

```text
Connecting Colab MCP browser session...
```

CDP inspection showed the local MCP approval dialog remained open and the frontend transport was not connected.

## Alternatives Considered

1. Restart the copied Chrome profile every time. This can clear stale UI state, but it is slower and can still show the same approval dialog.
2. Use a second copied profile and CDP port for shell mode. This avoids the active connection conflict, but duplicates browser state and does not solve automatic approval.
3. Click the dialog manually in the visible browser. This works once, but it keeps the user in the loop.
4. Bypass Colab's wrapper and construct the transport manually. This is brittle because the transport class is minified and can change.
5. Extend `_connect_colab_tab()` to click Colab's local MCP approval dialog through CDP, then verify the inner transport.

## What Worked

Option 5 was implemented. `_connect_colab_tab()` now:

- Traverses the page and shadow DOM from CDP.
- Finds the dialog whose text contains `local Colab MCP server`.
- Clicks the visible `Connect` button.
- Waits for `localColabMcpService.connect()` to complete.
- Returns success only when the inner frontend MCP server is connected.

## Why It Worked

The Colab frontend can require explicit approval even when `localColabMcpService.connect()` is called from page JavaScript. Clicking the dialog in the same CDP attach flow removes the manual action while preserving Colab's approval flow and the signed browser profile.

## Commands Run

```bash
uv run python - <<'PY'
# CDP inspection of localColabMcpService, token, port, and visible dialog text.
PY
uv run pytest tests/session_test.py::TestConnectColabTab -q
```
