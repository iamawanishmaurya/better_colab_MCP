# PinchTab xterm Text Canvas Wait Timeout

- Problem: [docs/problems/2026-06-06-pinchtab-xterm-text-canvas-wait-timeout.md](../problems/2026-06-06-pinchtab-xterm-text-canvas-wait-timeout.md)

## What Failed

The verification waited for `canvas.xterm-text-layer`:

```bash
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab wait --fn 'Boolean(window.term && document.querySelector("canvas.xterm-text-layer"))'
```

It timed out with:

```text
ERROR: wait: timeout
```

## What Worked

The verification used broader terminal readiness and visual evidence:

```bash
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab eval --json '({title: document.title, url: location.href, hasTerm: Boolean(window.term), rows: window.term && window.term.rows, cols: window.term && window.term.cols, terminalContainer: Boolean(document.querySelector("#terminal-container")), cursorCanvas: Boolean(document.querySelector("canvas.xterm-cursor-layer")), bodyTextLength: document.body.innerText.length})'
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab screenshot --format png -o /tmp/colab-opencode-pinchtab-fixed-waited.png
```

## Why It Worked

The terminal can render with a canvas stack that does not expose `canvas.xterm-text-layer` during the wait. The broader check verified that `window.term` existed, the title changed to `OpenCode-Colab`, the terminal dimensions were `132x58`, and the screenshot visibly showed the Opencode TUI.

## Commands Run

```bash
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab wait --fn 'Boolean(window.term && document.querySelector("canvas.xterm-text-layer"))'
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab eval --json '({title: document.title, url: location.href, hasTerm: Boolean(window.term), rows: window.term && window.term.rows, cols: window.term && window.term.cols, terminalContainer: Boolean(document.querySelector("#terminal-container")), textCanvas: Boolean(document.querySelector("canvas.xterm-text-layer")), cursorCanvas: Boolean(document.querySelector("canvas.xterm-cursor-layer")), bodyTextLength: document.body.innerText.length})'
PINCHTAB_SESSION=ses_bb804e402c7fc30071e7d15daa500a5ce96cf70a6dddf2bc pinchtab screenshot --format png -o /tmp/colab-opencode-pinchtab-fixed-waited.png
file /tmp/colab-opencode-pinchtab-fixed-waited.png
ls -lh /tmp/colab-opencode-pinchtab-fixed-waited.png
```

Result: screenshot `/tmp/colab-opencode-pinchtab-fixed-waited.png` displayed Opencode in Colab at `/content` with version `1.16.2`.
