# Signed CDP Opencode Drive Fallback

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-signed-cdp-opencode-drive-mount-failed.md](../problems/2026-06-07-signed-cdp-opencode-drive-mount-failed.md)

## What Failed

The strict signed-CDP Opencode bridge connected MCP and the runtime, then failed during setup because `google.colab.drive.mount("/content/drive")` returned `ValueError: mount failed`. The setup aborted because `REQUIRE_DRIVE=True`.

## Alternatives Considered

1. Keep strict Drive and ask for manual Drive authorization. This preserves Drive-backed recovery, but it blocks automated startup.
2. Use `--no-require-drive` while keeping Drive persistence enabled. This still attempts Drive, records the failure, falls back to `/content`, and lets Opencode start.
3. Disable Drive persistence entirely. This avoids the mount path, but loses the recovery intent and produces less useful diagnostics.
4. Try to automate the Drive OAuth prompt with CDP. This is brittle and can fail when Colab or Google changes the prompt flow.
5. Pre-stage files from the laptop into Colab without Drive. This can recover files for one runtime but does not solve persistent notebook/session recovery.

## What Worked

Option 2 worked for live startup:

```bash
tmux new-session -d -s colab-opencode-ghosttown-cdp-fixed 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --no-require-drive --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --log-file /tmp/colab-mcp-opencode-cdp-fixed-fallback-mcp.log > /tmp/colab-mcp-opencode-cdp-fixed-fallback.log 2>&1'
```

## Why It Worked

The setup cell can continue when Drive is unavailable if strict Drive is disabled. It emits a structured `COLAB_OPENCODE_RESULT` with `drive.mounted=false`, starts Opencode in `/content`, starts Ghost Town on the Colab port, and exposes the local proxy.

## Commands Run

```bash
tmux kill-session -t colab-opencode-ghosttown-cdp-fixed
rm -f /tmp/colab-mcp-opencode-cdp-fixed-fallback.log /tmp/colab-mcp-opencode-cdp-fixed-fallback-mcp.log
tmux new-session -d -s colab-opencode-ghosttown-cdp-fixed 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --no-require-drive --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --log-file /tmp/colab-mcp-opencode-cdp-fixed-fallback-mcp.log > /tmp/colab-mcp-opencode-cdp-fixed-fallback.log 2>&1'
tail -n 220 /tmp/colab-mcp-opencode-cdp-fixed-fallback.log
ss -ltnp | rg ':(8768|7685|9463)\b'
```

## Evidence

```text
opencode --version
1.16.2

ghosttown --version
1.9.1

COLAB_OPENCODE_RESULT {"drive": {"enabled": true, "mounted": false}, "ok": true, "portOpen": true, "terminalBackend": "ghosttown", "ghosttownSessionMode": "tmux", "ghosttownTmuxSession": "opencode", "workdir": "/content"}

Localhost URL: http://127.0.0.1:8768
Ghost Town new Opencode session URL: http://127.0.0.1:8768/new
Localhost smoke: {"ok": true, "status": 200}
```
