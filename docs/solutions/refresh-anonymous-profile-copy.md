# Refresh Anonymous Profile Copy

## Problem Link

- [Drive launcher reused profile login required](../problems/2026-06-07-drive-launcher-reused-profile-login-required.md)
- [Copied profile Colab login required](../problems/2026-06-07-copied-profile-colab-login-required.md)

## What Failed

The launcher reused `/tmp/colab-mcp-opencode-realcopy-profile`, but that copied profile was anonymous in Colab. MCP connected, but runtime connection failed because Colab required login. Reusing the same copied profile preserved the bad auth state.

## What Worked

Add `--refresh-profile-copy` to the launcher and switch to the actual consented Chrome profile. Local Chrome metadata showed `Default` belonged to `nothumanatall / canbehumanagain@gmail.com`, but `is_consented_primary_account=false`. `Profile 32` was the only profile with `is_consented_primary_account=true`.

This command solved the login-required runtime blocker:

```bash
./scripts/launch_colab_drive_terminal.sh shell \
  --profile 'Profile 32' \
  --profile-copy-dir /tmp/colab-mcp-profile32-copy \
  --refresh-profile-copy \
  --no-open \
  --no-tail \
  --exit-after-smoke
```

The log then showed:

```text
Connected to Colab MCP. Browser connected=True
Runtime status: ... "loginRequired": false ... "hasRuntime": true ...
```

## Why It Worked

The copied-profile reuse feature is correct after the dedicated copy is signed in, but it should not be forced when the copy is known to be anonymous. Refreshing the copy gives the user a one-command recovery path while preserving the default reuse behavior for normal reconnects. Selecting `Profile 32` mattered because it was the only currently consented Chrome profile in the local registry.

The next blocker is separate from login: strict Google Drive mount still requires Drive authorization in Colab.

## Commands Run

```bash
./scripts/launch_colab_drive_terminal.sh shell --no-open --no-tail --exit-after-smoke
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_id} #{pane_pid} #{pane_current_command} dead=#{pane_dead} status=#{pane_dead_status}'
tail -n 160 /tmp/colab-mcp-colab-drive-terminal-cdp-shell-20260607-101416.log
tail -n 120 /tmp/colab-mcp-colab-drive-terminal-cdp-shell-20260607-101416-mcp.log
ss -ltnp
jq -r '.profile.info_cache | to_entries[] | [.key, .value.name, .value.gaia_name, .value.gaia_given_name, .value.user_name, (.value.is_consented_primary_account|tostring), (.value.active_time|tostring)] | @tsv' /home/astra/.config/google-chrome/'Local State'
./scripts/launch_colab_drive_terminal.sh shell --profile 'Profile 32' --profile-copy-dir /tmp/colab-mcp-profile32-copy --refresh-profile-copy --no-open --no-tail --exit-after-smoke
```
