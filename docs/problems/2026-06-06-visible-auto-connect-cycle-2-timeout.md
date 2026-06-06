# Visible auto-connect cycle 2 timeout

- Timestamp: 2026-06-06T14:40:06+05:30
- Problem slug: visible-auto-connect-cycle-2-timeout

## Exact Error

The second live auto-connect cycle did not connect within 120 seconds after all three visible-browser key strategies ran.

```text
CYCLE 2 open redacted=https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>
CYCLE 2 connected=False elapsed=2
CYCLE 2 connected=False elapsed=4
CYCLE 2 connected=False elapsed=6
CYCLE 2 auto_attempt_1 ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'
CYCLE 2 connected=False elapsed=8
CYCLE 2 connected=False elapsed=10
CYCLE 2 connected=False elapsed=12
CYCLE 2 connected=False elapsed=14
CYCLE 2 auto_attempt_2 ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'
CYCLE 2 connected=False elapsed=17
CYCLE 2 connected=False elapsed=19
CYCLE 2 connected=False elapsed=21
CYCLE 2 connected=False elapsed=23
CYCLE 2 auto_attempt_3 ok=True reason=sent connect key sequence strategy=tab-tab-enter title='scratchpad - Colab - Google Chrome'
CYCLE 2 connected=False elapsed=26
...
CYCLE 2 connected=False elapsed=120
RuntimeError: cycle 2 did not connect; attempts=["ok=True reason=sent connect key sequence strategy=enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-enter title='scratchpad - Colab - Google Chrome'", "ok=True reason=sent connect key sequence strategy=tab-tab-enter title='scratchpad - Colab - Google Chrome'"]
```

## Reproduction Steps

1. Run the three-cycle live auto-connect probe.
2. Cycle 1 starts a fresh `uv run colab-mcp`, opens the scratch URL, sends visible key attempts, connects, and calls `get_cells`.
3. Cycle 2 starts another fresh `uv run colab-mcp`, opens a new scratch URL, sends `enter`, `tab-enter`, and `tab-tab-enter`.
4. Observe `connected=false` through the 120 second timeout.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: existing Chrome profile `Default`
- Window manager: Hyprland
- Visible automation: `hyprctl` plus `ydotool`
- Target window: `scratchpad - Colab - Google Chrome`
- Cycle 1 status: connected after 17 seconds and `get_cells` returned `cell_count=1`

## First Hypothesis

After cycle 1 exits, the Colab page can remain logically connected to the previous local MCP service or leave focus inside a state where simple `enter`/`tab` key sequences no longer activate the new Connect dialog. The current fallback sends key sequences but does not force a page reload or explicit stale-service reset in non-CDP Chrome.
