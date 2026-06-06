# Visible auto-connect cycle 2 timeout repeated

- Timestamp: 2026-06-06T14:47:28+05:30
- Problem slug: visible-auto-connect-cycle-2-timeout-repeat

## Exact Error

After changing the first visible auto-connect attempt to open a fresh Chrome window with the scratch URL, the second live cycle still failed to connect within 150 seconds.

```text
CYCLE 2 open redacted=https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>
CYCLE 2 connected=False elapsed=2
CYCLE 2 connected=False elapsed=4
CYCLE 2 connected=False elapsed=6
CYCLE 2 auto_attempt_1 ok=True reason=opened scratch URL and sent connect key strategy=new-window-url-enter title='scratchpad - Colab - Google Chrome'
CYCLE 2 connected=False elapsed=25
CYCLE 2 auto_attempt_2 ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'
CYCLE 2 auto_attempt_3 ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'
CYCLE 2 auto_attempt_4 ok=True reason=sent connect key sequence strategy=tab-tab-enter title='scratchpad - Colab - Google Chrome'
...
CYCLE 2 connected=False elapsed=151
RuntimeError: cycle 2 did not connect; attempts=["ok=True reason=opened scratch URL and sent connect key strategy=new-window-url-enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-tab-enter title='scratchpad - Colab - Google Chrome'"]
```

## Reproduction Steps

1. Run the fixed three-cycle live auto-connect probe with four attempts per cycle.
2. Cycle 1 connects and verifies `get_cells`.
3. Cycle 2 opens a new scratch URL and runs all four visible auto-connect attempts.
4. Observe that the MCP connection remains false until timeout.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: existing Chrome profile `Default`
- Window manager: Hyprland
- Visible automation: `hyprctl` plus `ydotool`
- Cycle 1 result after fix: connected after 36 seconds and `get_cells` returned `cell_count=1`

## First Hypothesis

Keyboard-only dialog automation is not deterministic enough for repeated short-lived MCP sessions in an existing multi-tab Chrome profile. Colab's local MCP service can remain stale after the previous server exits, and without CDP or a browser-side script, the local process cannot reliably call `localColabMcpService.disconnect()` or `connect()` directly.
