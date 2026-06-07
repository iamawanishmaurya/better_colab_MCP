# Drive Launcher Reused Profile Login Required

## Exact Error

The new launcher started correctly and connected the Colab MCP browser session, but runtime connection failed because the reused copied Chrome profile is anonymous in Colab:

```text
Connecting Colab MCP browser session...
Connected to Colab MCP. Browser connected=True
RuntimeError: Colab runtime did not connect: {'ok': False, 'steps': [], 'warnings': ['Colab login is required in the dedicated MCP browser before connecting a runtime.'], ... 'loginRequired': True, ... 'text': 'Sign in' ...}
```

The tmux pane exited with status `1`:

```text
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_id} #{pane_pid} #{pane_current_command} dead=#{pane_dead} status=#{pane_dead_status}'
%77 381682 colab-mcp-colab-drive-terminal-cdp-shell-20260607-101416.runner.sh dead=1 status=1
```

The fresh launcher log was:

```text
/tmp/colab-mcp-colab-drive-terminal-cdp-shell-20260607-101416.log
```

## Reproduction Steps

1. Run the new launcher with a reused copied Chrome profile:

   ```bash
   ./scripts/launch_colab_drive_terminal.sh shell --no-open --no-tail --exit-after-smoke
   ```

2. The launcher creates a fresh tmux runner and starts controlled Chrome on CDP port `9463`.
3. MCP connects successfully.
4. `connect_runtime` fails because Colab shows `Sign in` in the controlled copied profile.

## Environment

- Timestamp: `2026-06-07T10:16:02+05:30`
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Launcher: `scripts/launch_colab_drive_terminal.sh`
- Mode: `shell`
- Profile copy dir: `/tmp/colab-mcp-opencode-realcopy-profile`
- Source profile: `/home/astra/.config/google-chrome` / `Default`
- CDP port: `9463`
- Local port: `8768`
- Colab port: `7686`

## First Hypothesis

The launcher correctly preserves an existing copied profile, but the preserved copy is already logged out or was created before the real source profile was authenticated. Because `_ensure_controlled_edge()` returns immediately when the CDP port is alive, a stale anonymous controlled Chrome process can also keep the bad copied profile active. The launcher needs a refresh mode that stops the controlled Chrome process and passes `--no-browser-reuse-profile-copy` so the copied profile is rebuilt from the real signed `Default` profile.
