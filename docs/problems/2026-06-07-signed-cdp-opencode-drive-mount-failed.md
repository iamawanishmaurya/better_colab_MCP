# Signed CDP Opencode Drive Mount Failed

- Date: 2026-06-07
- Area: Signed CDP Opencode localhost bridge

## Exact Error

```text
ValueError: mount failed

RuntimeError: Google Drive mount failed. Complete the Colab Drive authorization prompt and rerun setup.

RuntimeError: Opencode setup did not emit COLAB_OPENCODE_RESULT.
```

The failing setup cell output included:

```text
File "/tmp/ipykernel_412/3011888408.py", line 91, in mount_drive
    drive.mount("/content/drive", force_remount=False)

File "/usr/local/lib/python3.12/dist-packages/google/colab/drive.py", line 272, in _mount
    raise ValueError('mount failed' + extra_reason)

RuntimeError: Google Drive mount failed. Complete the Colab Drive authorization prompt and rerun setup.
```

## Reproduction Steps

1. Start the signed CDP Ghost Town tmux localhost bridge with strict Drive requirement:

   ```bash
   tmux new-session -d -s colab-opencode-ghosttown-cdp-fixed 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 240 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --log-file /tmp/colab-mcp-opencode-cdp-fixed-mcp.log > /tmp/colab-mcp-opencode-cdp-fixed.log 2>&1'
   ```

2. Wait for MCP attach and runtime connect to succeed.
3. Inspect `/tmp/colab-mcp-opencode-cdp-fixed.log` or the generated Colab setup cell output.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: signed-in headed copied Chrome profile on CDP port `9463`
- Google account shown in Colab: `canbehumanagain@gmail.com`
- Local tmux session: `colab-opencode-ghosttown-cdp-fixed`
- Local proxy port requested: `8768`
- Colab service port requested: `7685`
- Runtime: Python `3.12.13`, cwd `/content`

## First Hypothesis

The signed-in browser can connect MCP and the runtime, but Colab Drive mount still requires a separate Drive authorization flow. Strict `REQUIRE_DRIVE=True` correctly aborts before Opencode starts when Drive cannot mount.
