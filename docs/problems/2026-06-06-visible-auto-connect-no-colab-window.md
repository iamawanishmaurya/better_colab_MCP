# Visible auto-connect no Colab window

- Timestamp: 2026-06-06T14:56:34+05:30
- Problem slug: visible-auto-connect-no-colab-window

## Exact Error

The reconnect live test failed because the visible automation helper could not find a Chrome window with a Colab title:

```text
RECONNECT CYCLE 1 auto_attempt_1 ok=False reason=no visible Chrome Colab window
RECONNECT CYCLE 1 auto_attempt_2 ok=False reason=no visible Chrome Colab window
RECONNECT CYCLE 1 auto_attempt_3 ok=False reason=no visible Chrome Colab window
RECONNECT CYCLE 1 auto_attempt_4 ok=False reason=no visible Chrome Colab window
...
RuntimeError: reconnect cycle 1 failed; attempts=['ok=False reason=no visible Chrome Colab window', 'ok=False reason=no visible Chrome Colab window', 'ok=False reason=no visible Chrome Colab window', 'ok=False reason=no visible Chrome Colab window']
```

## Reproduction Steps

1. Run the single-server reconnect live test after the active Chrome tab is not a Colab scratchpad tab.
2. The helper searches Chrome windows for a title matching `Colab`.
3. No matching title is present, so all auto-connect attempts return `no visible Chrome Colab window`.
4. The MCP connection remains false until timeout.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: existing Chrome profile `Default`
- Window manager: Hyprland
- Visible automation: `hyprctl` plus `ydotool`

## First Hypothesis

The helper is too strict when a target scratch URL is available. If no Colab-titled Chrome window exists, it should focus any visible Chrome/Chromium window and open the target URL in a new Chrome window before sending Connect-dialog keys.
