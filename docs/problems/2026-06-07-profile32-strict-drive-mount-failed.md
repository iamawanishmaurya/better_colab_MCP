# Profile32 Strict Drive Mount Failed

## Exact Error

Using the authenticated `Profile 32` copied profile got past the Colab login/runtime blocker, but the strict Drive-backed setup failed:

```text
Runtime status: {"after": {"hasKernel": true, "hasNotebook": true, "hasRuntime": true, "hasTerminalConnection": true, ... "loginRequired": false, ...}}
```

Then the setup cell failed during Drive mount:

```text
ValueError: mount failed
...
RuntimeError: Google Drive mount failed. Complete the Colab Drive authorization prompt and rerun setup.
...
RuntimeError: Opencode setup did not emit COLAB_OPENCODE_RESULT.
```

The local launcher pane exited:

```text
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_id} #{pane_pid} #{pane_current_command} dead=#{pane_dead} status=#{pane_dead_status}'
%79 410091 colab-mcp-colab-drive-terminal-cdp-shell-20260607-102045.runner.sh dead=1 status=1
```

## Reproduction Steps

1. Run the launcher against the only consented Chrome profile:

   ```bash
   ./scripts/launch_colab_drive_terminal.sh shell \
     --profile 'Profile 32' \
     --profile-copy-dir /tmp/colab-mcp-profile32-copy \
     --refresh-profile-copy \
     --no-open \
     --no-tail \
     --exit-after-smoke
   ```

2. MCP connects successfully.
3. Runtime connection succeeds with `loginRequired=false`.
4. The generated setup cell calls `drive.mount("/content/drive")`.
5. Colab Drive mount fails, and strict `--require-drive` stops setup before `COLAB_OPENCODE_RESULT` is emitted.

## Environment

- Timestamp: `2026-06-07T10:31:05+05:30`
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Launcher: `scripts/launch_colab_drive_terminal.sh`
- Browser profile: `Profile 32`
- Profile copy dir: `/tmp/colab-mcp-profile32-copy`
- CDP port: `9463`
- Local port: `8768`
- Colab port: `7686`
- Drive mode: strict `--require-drive`

## First Hypothesis

The browser profile is authenticated enough for Colab runtime connection, but Google Drive authorization is a separate Colab OAuth step. The terminal can be smoke-tested with `--no-require-drive`, but the desired Drive-primary disk mode still requires the user to complete the Drive authorization prompt once in the visible Colab browser session.
