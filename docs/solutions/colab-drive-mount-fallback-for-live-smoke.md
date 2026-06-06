# Colab Drive Mount Fallback For Live Smoke

- Date: 2026-06-06
- Problem: `docs/problems/2026-06-06-colab-drive-mount-failed-live.md`

## What Failed

The strict Ghost Town live setup required Google Drive to mount before continuing. In the active Colab runtime, `google.colab.drive.mount("/content/drive", force_remount=False)` failed without interactive authorization, so the setup cell did not emit `COLAB_OPENCODE_RESULT`.

## What Worked

The same live Ghost Town setup succeeded with `--no-require-drive`. The setup still attempted Drive, recorded the mount timeout in the emitted result, then fell back to `/content` and continued installing/starting OpenCode and Ghost Town.

## Why It Worked

Drive persistence and Drive strictness are separate controls. Keeping Drive persistence enabled allows normal runs to mount and persist state by default, while disabling strict Drive requirement lets automated smoke tests validate the terminal/backend path when Colab Drive authorization is not available.

## Commands Run

```bash
tmux kill-session -t colab-opencode-ghosttown
rm -f /tmp/colab-mcp-opencode-ghosttown.log /tmp/colab-mcp-opencode-ghosttown-mcp.log
tmux new-session -d -s colab-opencode-ghosttown 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --no-require-drive --colab-port 7682 --local-port 8766 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 60 --log-file /tmp/colab-mcp-opencode-ghosttown-mcp.log > /tmp/colab-mcp-opencode-ghosttown.log 2>&1'
ss -ltnp 'sport = :8766'
tail -80 /tmp/colab-mcp-opencode-ghosttown.log
```

## Evidence

```text
$ opencode --version
1.16.2

$ ghosttown --version
1.9.1

COLAB_OPENCODE_RESULT {"drive": {"enabled": true, "error": "DriveMountTimeout('Google Drive mount timed out after 60 seconds')", "folder": "/content/drive/MyDrive/opencode", "mounted": false}, "ok": true, "portOpen": true, "terminalBackend": "ghosttown", "workdir": "/content"}

Localhost URL: http://127.0.0.1:8766
Ghost Town new Opencode session URL: http://127.0.0.1:8766/new
Localhost smoke: {"ok": true, "status": 200}
```
