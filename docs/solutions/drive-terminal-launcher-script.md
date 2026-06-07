# Drive Terminal Launcher Script

## Problem Link

- [Wrapped tmux command stale log](../problems/2026-06-07-wrapped-tmux-command-stale-log.md)
- [Runtime connect urlopen connection refused](../problems/2026-06-07-runtime-connect-urlopen-connection-refused.md)

## What Failed

The manual launch command was too long and fragile for repeated interactive use. When it wrapped inside the single-quoted tmux command, tmux exited with status `127` before the new bridge started. The terminal then tailed an older log and displayed the previous runtime-connect refusal, making the failure look like a fresh Colab runtime error.

The runtime-connect refusal has also appeared more than once. Repeating the same "rerun the long command" fix would not address the underlying fragility.

## Alternatives Evaluated

1. Rerun the same long tmux command with corrected line continuations.
   - Fast, but still fragile and easy to paste incorrectly.
   - Does not prevent stale log confusion.

2. Use the real Chrome `Default` profile directly with CDP.
   - Would avoid copied-profile login drift.
   - Chrome blocks remote debugging on the default data directory in this environment, so this path is not reliable.

3. Skip runtime connect after MCP approval.
   - Can verify the browser-to-MCP transport.
   - Cannot set up the Drive-backed terminal, because the setup cell needs a connected Colab runtime.

4. Add only better diagnostics around `connect_runtime`.
   - Useful for future runtime failures.
   - Does not solve the current command-wrap and stale-log launch failure.

5. Add a short launcher script that owns tmux, fresh logs, and localhost opening.
   - Removes the pasted long command from the user workflow.
   - Uses a fresh log path per run so old runtime errors are not mistaken for current output.
   - Keeps `shell` and `opencode` modes selectable while preserving the Drive-backed defaults.

## What Worked

The selected fix is a repository launcher script that starts the existing Python bridge with Bash arrays, writes a temporary tmux runner file, waits for `http://127.0.0.1:<port>/new`, and opens it when the local proxy is actually listening.

## Why It Worked

The shell array path avoids option splitting caused by wrapped command text. The fresh log path removes stale-tail ambiguity. Waiting for the local port before opening `/new` matches the real bridge lifecycle, because localhost is not available until MCP connects, the runtime connects, the terminal starts inside Colab, proxy cookies are collected, and the local reverse proxy binds.

## Commands Run

```bash
tmux list-panes -t colab-drive-terminal-cdp -F '#{pane_id} #{pane_pid} #{pane_current_command} dead=#{pane_dead} status=#{pane_dead_status}'
ss -ltnp
pgrep -af 'colab_opencode_localhost|remote-debugging-port=9463|browser-profile-copy-dir|colab-mcp-shell-mode-live|--colab-port 7686|--local-port 8768'
curl -sS http://127.0.0.1:9463/json/version
curl -sS http://127.0.0.1:8768/new
stat -c '%y %s %n' /tmp/colab-mcp-shell-mode-live.log /tmp/colab-mcp-shell-mode-live-mcp.log
```
