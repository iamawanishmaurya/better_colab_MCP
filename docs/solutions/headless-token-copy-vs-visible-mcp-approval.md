# Headless Token Copy Vs Visible MCP Approval

Problem files:

- [../problems/2026-06-07-runtime-reconnect-login-required.md](../problems/2026-06-07-runtime-reconnect-login-required.md)
- [../problems/2026-06-07-runtime-connect-urlopen-connection-refused.md](../problems/2026-06-07-runtime-connect-urlopen-connection-refused.md)
- [../problems/2026-06-07-ghosttown-tmux-setup-missing-result-marker.md](../problems/2026-06-07-ghosttown-tmux-setup-missing-result-marker.md)

## What Failed

Copying or reusing the MCP proxy token in a headless or copied Chrome profile did not solve runtime connection. The repository already has the CDP implementation for this flow: `_connect_colab_tab()` sets `mcp_proxy_token`, sets `mcp_proxy_port`, updates the hash URL, and calls `localColabMcpService.connect()`.

The copied/headless browser connected to the local MCP frontend but Colab reported `loginRequired=true`. That means the token connected the notebook to the local MCP server, but it did not authenticate the Google/Colab runtime session.

## Evaluated Options

1. Headless copied profile with token automation.
   - Trade-off: fully automatic if authenticated.
   - Result: rejected for the current machine because Colab reports `loginRequired=true`.

2. Headed copied profile with token automation.
   - Trade-off: visible and CDP-controllable.
   - Result: rejected because the copied profile still showed `Sign in` / `loginRequired=true`.

3. Copy the visible token and paste it into headless.
   - Trade-off: would reuse the same MCP server coordinates.
   - Result: rejected because the token does not carry Google auth, and the token becomes stale when the local MCP process exits.

4. Use the real visible Chrome `Default` profile and approve the dialog there.
   - Trade-off: preserves the user's live browser state, but OS-level automation is less clean than CDP.
   - Result: selected for MCP approval. It advanced the launcher to `Connected to Colab MCP. Browser connected=True`.

5. Relaunch the real Chrome profile with remote debugging.
   - Trade-off: would allow clean CDP automation in the authenticated profile.
   - Result: not selected because it would require closing or disrupting the user's active Chrome session.

## What Worked

The visible MCP approval dialog was accepted in the real browser using OS-level pointer movement and click automation. The bridge log advanced to:

```text
Connected to Colab MCP. Browser connected=True
```

## What Still Failed

The later runtime connection still failed:

```text
RuntimeError: Colab runtime did not connect: {'text': '<urlopen error [Errno 111] Connection refused>'}
```

The visible Colab page also showed a `Sign in` button, so the remaining blocker is not MCP token approval. It is an authenticated Colab runtime session.

## Why It Worked

The MCP approval dialog is a notebook-local security gate. Clicking `Connect` in the visible tab authorizes that notebook page to talk to the local MCP server. This validates the visible approval path.

## Why Headless Token Copy Did Not Work

The MCP proxy token only authorizes the local MCP connection. It does not prove Google login, does not connect a Colab runtime, and does not transfer browser cookies from a signed-in tab to a copied/headless profile.

## Commands Run

```bash
tmux new-session -d -s colab-opencode-ghosttown-visible-tmux 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 180 --no-browser-headless --browser-profile-copy-dir /tmp/colab-mcp-opencode-visible-profile-copy --cdp-port 9461 --log-file /tmp/colab-mcp-opencode-ghosttown-visible-tmux-mcp.log > /tmp/colab-mcp-opencode-ghosttown-visible-tmux.log 2>&1'
kill 28508
tmux new-session -d -s colab-opencode-ghosttown-default-tmux 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 180 --no-browser-headless --no-browser-copy-profile --browser-profile Default --cdp-port 9462 --log-file /tmp/colab-mcp-opencode-ghosttown-default-tmux-mcp.log > /tmp/colab-mcp-opencode-ghosttown-default-tmux.log 2>&1'
grim /tmp/colab-default-mcp-dialog.png
ydotool mousemove -x -214 -y -361
ydotool mousemove -x 97 -y 164
ydotool mousemove -x 81 -y 137
ydotool click 0xC0
tail -100 /tmp/colab-mcp-opencode-ghosttown-default-tmux.log
ss -ltnp 'sport = :8768'
```
