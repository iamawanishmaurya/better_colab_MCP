# Single-server reconnect cycle 2 timeout

- Timestamp: 2026-06-06T15:02:46+05:30
- Problem slug: single-server-reconnect-cycle-2-timeout

## Exact Error

A single local MCP server successfully connected once, then detected a browser frontend disconnect after closing the scratch tab, but the second visible reconnect cycle did not reconnect.

```text
RECONNECT CYCLE 1 RESULT connected_at=33 attempts=["ok=True reason=opened scratch URL and sent connect key strategy=new-window-url-enter title='Alien Txtbase Pipeline - Google Chrome'", "ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'"] cell_count=1
RECONNECT CYCLE 1 close title='scratchpad - Colab - Google Chrome' focused=True ctrl_w=True
RECONNECT CYCLE 1 disconnect_wait connected=False elapsed=6
RECONNECT CYCLE 2 auto_attempt_1 ok=True reason=opened scratch URL and sent connect key strategy=new-window-url-enter title='Alien Txtbase Pipeline - Google Chrome'
RECONNECT CYCLE 2 auto_attempt_2 ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'
RECONNECT CYCLE 2 auto_attempt_3 ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'
RECONNECT CYCLE 2 auto_attempt_4 ok=True reason=sent connect key sequence strategy=tab-tab-enter title='scratchpad - Colab - Google Chrome'
...
RuntimeError: reconnect cycle 2 failed; attempts=["ok=True reason=opened scratch URL and sent connect key strategy=new-window-url-enter title='Alien Txtbase Pipeline - Google Chrome'", "ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-tab-enter title='scratchpad - Colab - Google Chrome'"]
```

## Reproduction Steps

1. Start one client-managed `uv run colab-mcp` server.
2. Use visible automation to open the scratch URL and accept the Connect dialog.
3. Verify `get_cells` succeeds.
4. Close the scratch tab with `Ctrl+W`.
5. Wait until `get_connection_info.connected` becomes false.
6. Reopen the same scratch URL and run four visible auto-connect attempts.
7. Observe that the browser frontend does not reconnect.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: existing Chrome profile `Default`
- Window manager: Hyprland
- Visible automation: `hyprctl` plus `ydotool`
- Local reconnect loop: enabled in `ColabProxyClient`

## First Hypothesis

The local reconnect loop works, but Colab's browser-side `localColabMcpService` still needs a direct reset/connect call after a prior frontend disconnect. Keyboard automation can activate the first confirmation dialog, but it cannot reliably reset stale browser-side service state after reconnect.
