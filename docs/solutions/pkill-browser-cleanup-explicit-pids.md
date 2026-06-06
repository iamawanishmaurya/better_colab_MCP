# Browser Cleanup With Explicit Process Discovery

Problem file: [../problems/2026-06-07-pkill-browser-cleanup-pattern-self-match.md](../problems/2026-06-07-pkill-browser-cleanup-pattern-self-match.md)

## What Failed

The live Ghost Town tmux smoke cleanup used a broad command:

```bash
pkill -f 'remote-debugging-port=9460|user-data-dir=/tmp/colab-mcp-opencode-tmux-profile-copy' || true
```

That command exited with code `-1` and no stderr. The likely failure mode was the command matching its own shell/process text while trying to clean Chrome.

## What Worked

Explicit process discovery showed that no cleanup target remained:

```bash
ss -ltnp 'sport = :9460' || true
pgrep -af '([r]emote-debugging-port=9460|[u]ser-data-dir=/tmp/colab-mcp-opencode-tmux-profile-copy)' || true
tmux list-sessions 2>/dev/null | rg 'colab-opencode-ghosttown-tmux|opencode' || true
```

The CDP listener check returned only the `ss` header, the guarded `pgrep` returned no process rows, and the tmux list showed only the existing non-tmux-smoke sessions.

## Why It Worked

The `ss` command checks the exact CDP port without matching command-line text. The guarded `pgrep` regex uses bracketed first characters (`[r]emote`, `[u]ser-data-dir`) so the discovery command does not match itself while still matching real browser command lines.

## Commands Run

```bash
ss -ltnp 'sport = :9460' || true
pgrep -af '([r]emote-debugging-port=9460|[u]ser-data-dir=/tmp/colab-mcp-opencode-tmux-profile-copy)' || true
tmux list-sessions 2>/dev/null | rg 'colab-opencode-ghosttown-tmux|opencode' || true
```
