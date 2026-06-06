# Fresh MCP cell execution hang

- Timestamp: 2026-06-06T14:23:00+05:30
- Problem file: `docs/problems/2026-06-06-fresh-mcp-cell-execution-hang.md`

## What Failed

A fresh MCP browser connection succeeded, but `run_code_cell` did not return from a simple print probe. This was the second notebook-cell execution hang in the same flow.

## Evaluated Options

1. Wait longer: rejected because two cell executions had already hung.
2. Relaunch Chrome with CDP: technically strong, but disruptive because it requires closing the logged-in Chrome profile.
3. Trigger Colab interrupt in the visible Chrome window: selected because it targets the blocked execution slot without restarting the browser or runtime.
4. Restart the whole Colab runtime: useful fallback, but more destructive because it loses runtime state.
5. Use a separate authenticated browser/profile: not available without another logged-in Colab session.

## What Worked

Hyprland focused the visible Colab Chrome window, then `ydotool` sent `Esc`, `Ctrl+M`, and `I`. A fresh bounded MCP probe then connected and ran:

```python
print('post-interrupt-probe-ok-20260606')
```

The output returned `post-interrupt-probe-ok-20260606` with `probeOk True`.

## Why It Worked

`Ctrl+M`, then `I`, is Colab's interrupt-execution shortcut. It released the stuck notebook execution slot while preserving the runtime.

## Commands Run

```sh
hyprctl clients -j | jq -r '.[] | select(.class=="google-chrome") | [.address,.class,.title,.workspace.name] | @tsv'
hyprctl dispatch workspace 5
hyprctl dispatch focuswindow address:0x5790046a0d60
ydotool key 1:1 1:0 29:1 50:1 50:0 29:0 23:1 23:0
timeout 240s uv run python - <<'PY'
# Fresh MCP probe script that opened Colab, waited for connected=true,
# added a print cell, and verified post-interrupt-probe-ok-20260606.
PY
```
