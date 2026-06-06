# Ghost Town tmux MCP Connection With Isolated Browser State

Problem file: [../problems/2026-06-07-ghosttown-tmux-live-mcp-headless-connect-failed.md](../problems/2026-06-07-ghosttown-tmux-live-mcp-headless-connect-failed.md)

## What Failed

The first live Ghost Town tmux smoke reused the existing copied browser profile/CDP path. That run failed before the generated setup cell executed:

```text
RuntimeError: Colab MCP did not connect
```

The live tokens and URLs were redacted in the problem file.

## What Worked

Restarting the smoke with an isolated profile copy directory and a separate CDP port got past MCP connection:

```bash
uv run python scripts/colab_opencode_localhost.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --ghosttown-tmux-session opencode \
  --no-require-drive \
  --colab-port 7683 \
  --local-port 8767 \
  --setup-timeout 1200 \
  --install-timeout 900 \
  --drive-mount-timeout 60 \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-tmux-profile-copy \
  --cdp-port 9460 \
  --log-file /tmp/colab-mcp-opencode-ghosttown-tmux-mcp.log
```

That run connected MCP, then hit a separate login blocker documented in [../problems/2026-06-07-ghosttown-tmux-isolated-profile-login-required.md](../problems/2026-06-07-ghosttown-tmux-isolated-profile-login-required.md).

## Why It Worked

The isolated profile and CDP port avoided contention with the existing direct Ghost Town runs and the previous copied browser state. This resolved the initial MCP connection symptom, but the isolated profile was not authenticated for Colab runtime access.

## Commands Run

```bash
tmux kill-session -t colab-opencode-ghosttown-tmux
rm -rf /tmp/colab-mcp-opencode-tmux-profile-copy
uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --no-require-drive --colab-port 7683 --local-port 8767 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --browser-profile-copy-dir /tmp/colab-mcp-opencode-tmux-profile-copy --cdp-port 9460 --log-file /tmp/colab-mcp-opencode-ghosttown-tmux-mcp.log
```
