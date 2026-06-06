# PinchTab Wait Timed Out On xterm Text Canvas

- Timestamp: 2026-06-06T16:43:52+05:30
- Environment: PinchTab headed browser session `ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc`, local Opencode bridge `http://127.0.0.1:8765`, patched supervisor process PID `3202746`.

## Exact Error

```text
ERROR: wait: timeout
```

The timed-out command was:

```bash
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab wait --fn 'Boolean(window.term && document.querySelector("canvas.xterm-text-layer"))'
```

## Reproduction Steps

1. Open the patched local Opencode bridge in PinchTab:
   ```bash
   PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab nav http://127.0.0.1:8765 --snap
   ```
2. Wait for both `window.term` and `canvas.xterm-text-layer`:
   ```bash
   PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab wait --fn 'Boolean(window.term && document.querySelector("canvas.xterm-text-layer"))'
   ```
3. The wait times out even though the Opencode TUI later paints successfully.

## First Hypothesis

The Opencode/ttyd frontend can render through a canvas path that does not expose `canvas.xterm-text-layer` at the moment the wait checks it. The wait predicate was too specific for xterm's active renderer, so verification should use broader terminal readiness plus screenshot/title evidence.
