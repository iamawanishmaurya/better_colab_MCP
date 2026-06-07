# Colab Drive Terminal

This workflow opens a real browser-based PTY terminal inside a Colab runtime.
The default terminal is a native Colab Ubuntu shell rooted in Google Drive, so
Colab acts as disposable compute and Drive acts as the durable disk.

Run the interactive wizard:

```shell
uv run colab-drive-terminal
```

The wizard:

- Scans Chrome profiles from the local Chrome `Local State` file.
- Lets you select a signed-in Google profile by number or profile name.
- Uses a dedicated copied Chrome profile for controllable CDP/MCP automation.
- Connects Colab MCP without clicking the Colab dialog manually.
- Connects the Colab runtime.
- Mounts Google Drive by default.
- Opens a native Ubuntu shell in the Drive-backed project folder.
- Keeps `~/.config` and `~/.local/share` in Drive so app settings and sessions
  can recover after a Colab runtime reset.
- Keeps `~/.cache` temporary under `/content/colab-terminal-cache` by default.

The default persistent workspace is:

```text
/content/drive/MyDrive/colab-terminal/projects/<project-name>
```

OpenCode is not started by default. Install it inside the shell when needed:

```shell
curl -fsSL https://opencode.ai/install | bash
opencode
```

Useful wizard flags:

```shell
uv run colab-drive-terminal --profile 'Profile 32' --workspace drive --project my-project
uv run colab-drive-terminal --profile nothumanatall --workspace drive --project my-project
uv run colab-drive-terminal --profile 'Profile 32' --workspace temp --allow-temp --project scratch
uv run colab-drive-terminal --profile 'Profile 32' --refresh-profile-copy
uv run colab-drive-terminal --profile 'Profile 32' --dry-run
```

Use temporary `/content` mode only for disposable work. It is not durable across
Colab runtime resets.

## Lower-Level Setup Script

The lower-level setup script is still available when you want to bypass the
wizard:

```shell
uv run python scripts/colab_opencode_web_terminal.py
```

The script starts a client-managed `colab-mcp` server, opens Colab, mounts Drive
by default, installs the selected terminal backend, and opens a Colab output
window/iframe for the web terminal.

Useful flags:

```shell
uv run python scripts/colab_opencode_web_terminal.py --port 7682 --cwd /content/project
uv run python scripts/colab_opencode_web_terminal.py --setup-timeout 1200 --print-url
uv run python scripts/colab_opencode_web_terminal.py --no-auto-click-connect
uv run python scripts/colab_opencode_web_terminal.py --no-drive-persistence --cwd /content
uv run python scripts/colab_opencode_web_terminal.py --no-require-drive
uv run python scripts/colab_opencode_web_terminal.py --terminal-command shell
uv run python scripts/colab_opencode_web_terminal.py --terminal-command opencode
uv run python scripts/colab_opencode_web_terminal.py --terminal-backend ghosttown
uv run python scripts/colab_opencode_web_terminal.py --terminal-backend ghosttown --ghosttown-session-mode tmux
```

Use `--no-require-drive` only for smoke tests or temporary sessions where Drive
authorization is unavailable. It still attempts to mount Drive, but it falls
back to the requested runtime directory if Colab refuses or times out.

## Terminal Command Modes

The web terminal can open either a normal shell or Opencode:

```shell
# Recommended: plain Drive-rooted shell terminal with fresh logs and tmux.
./scripts/launch_colab_drive_terminal.sh shell

# Optional: start Opencode immediately in the Colab tmux session.
./scripts/launch_colab_drive_terminal.sh opencode

# Optional lower-level OpenCode mode.
uv run python scripts/colab_opencode_localhost.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --terminal-command opencode

# Plain terminal: open Bash in the Drive-backed project folder.
uv run python scripts/colab_opencode_localhost.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --terminal-command shell
```

When Drive mounts and `--cwd` is left as `/content`, both modes start in:

```text
/content/drive/MyDrive/colab-terminal/projects/project
```

That makes Google Drive the primary project disk for the terminal. OpenCode is
installed automatically only in OpenCode mode; in shell mode, install it from
the shell when needed.

The launcher script is the safest local entrypoint for repeated use. It avoids
long pasted tmux commands, creates fresh log files for every run, replaces the
old local tmux session by default, waits until localhost is actually listening,
and then opens:

```text
http://127.0.0.1:8768/new
```

Useful launcher overrides:

```shell
./scripts/launch_colab_drive_terminal.sh shell --no-require-drive
./scripts/launch_colab_drive_terminal.sh shell --refresh-profile-copy
./scripts/launch_colab_drive_terminal.sh shell --local-port 8769 --colab-port 7687
./scripts/launch_colab_drive_terminal.sh opencode --browser-headless
./scripts/launch_colab_drive_terminal.sh shell --no-tail
```

Use `--refresh-profile-copy` when the controlled browser shows `Sign in` even
though your real Chrome `Default` profile is signed in. It stops the controlled
Chrome process for the selected CDP/profile copy and rebuilds the dedicated copy
from the source profile.

On this machine, the signed Colab runtime profile is currently `Profile 32`, not
`Default`. Use this when the `Default` copy shows `Sign in`:

```shell
./scripts/launch_colab_drive_terminal.sh shell \
  --profile 'Profile 32' \
  --profile-copy-dir /tmp/colab-mcp-profile32-copy \
  --refresh-profile-copy
```

## Ghost Town Backend

Ghostty itself is a native desktop terminal, not a Colab web server. For a
browser-based Ghostty-powered terminal, use Ghost Town:

```shell
uv run python scripts/colab_opencode_web_terminal.py \
  --terminal-backend ghosttown \
  --drive-folder /content/drive/MyDrive/colab-terminal \
  --notebook-name colab-terminal.ipynb
```

The setup cell installs `@seflless/ghosttown`, writes
`/content/colab-terminal-ghosttown-shell.sh`, and starts the Ghost Town web server on
the selected Colab port. Open `/new` on the Ghost Town URL to create a
web-managed terminal session that launches either Bash or OpenCode in the
persistent project directory, depending on `--terminal-command`.

To make the Ghost Town browser terminal attach directly to a tmux session in
Colab, use tmux mode:

```shell
uv run python scripts/colab_opencode_web_terminal.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --ghosttown-tmux-session opencode
```

In tmux mode, setup installs `tmux`, creates or reuses the named tmux session,
starts the selected terminal command inside that session, and makes every Ghost
Town `/new` terminal attach to it. This is still not SSH; it is Ghost Town's
browser PTY connected to Colab's kernel port proxy.

For localhost access through the local reverse proxy:

```shell
uv run python scripts/colab_opencode_localhost.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --local-port 8765
```

When the bridge prints `Ghost Town new Opencode session URL` or
`Ghost Town new shell session URL`, open that `/new` URL to create the terminal
session.

For supervised reconnects:

```shell
uv run python scripts/colab_opencode_supervisor.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --local-port 8765
```

The supervisor keeps the same Enter-to-reconnect loop. For Ghost Town, health
checks verify HTTP availability; ttyd-specific `/ws` protocol probing is only
used for the `ttyd` backend.

## Localhost Without SSH

Use `scripts/colab_opencode_localhost.py` when you want the Colab-hosted
Opencode PTY to be reachable from this laptop as `localhost`.

```shell
uv run python scripts/colab_opencode_localhost.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-reuse-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765
```

The script:

- Connects Colab MCP through copied-profile headless CDP.
- Reuses an existing copied profile by default, so a dedicated Colab MCP browser
  login is not wiped on reconnect. Use `--no-browser-reuse-profile-copy` only
  when you intentionally want a fresh copy from the source Chrome profile.
- Starts controlled Chrome with local-network websocket checks disabled for the
  dedicated MCP profile. This avoids Chrome 148 blocking Colab's HTTPS page from
  reaching the local MCP websocket. Set
  `COLAB_MCP_BROWSER_DISABLE_LOCAL_NETWORK_CHECKS=0` to opt out.
- Connects the Colab runtime.
- Mounts Drive by default and prepares the persistent Colab terminal folder.
- Installs the selected web terminal backend on the remote Colab port.
- Reads the Colab kernel proxy URL.
- Starts a local HTTP/WebSocket reverse proxy at `http://127.0.0.1:8765`.
- Runs a localhost smoke request before staying attached.

For non-interactive validation:

```shell
uv run python scripts/colab_opencode_localhost.py --exit-after-smoke
```

This is not SSH. It is a local reverse proxy to Colab's kernel port proxy. If
the Colab runtime stops, the local URL will stop working until the script is run
again.

## Enter-To-Reconnect Supervisor

Use `scripts/colab_opencode_supervisor.py` when you want the bridge to record
session state and wait for Enter before reconnecting after the local or Colab
session dies.

```shell
uv run python scripts/colab_opencode_supervisor.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-reuse-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765
```

The supervisor writes state to:

```text
/tmp/colab-mcp-opencode-session-state.json
```

When health checks fail or the bridge exits, it marks the session `dead` and
prints:

```text
Session is down. Press Enter to reconnect Colab MCP and the terminal, or Ctrl+C to stop.
```

Press Enter in the supervisor terminal to restart the MCP connection, reconnect
the Colab runtime, restart the terminal backend, and restore localhost access.

To keep the supervisor attachable across shell interruptions, run it in tmux:

```shell
tmux new-session -s colab-opencode-supervisor
uv run python scripts/colab_opencode_supervisor.py \
  --browser-user-data-dir /home/astra/.config/google-chrome \
  --browser-profile Default \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-profile-copy \
  --browser-reuse-profile-copy \
  --browser-headless \
  --cdp-port 9458 \
  --local-port 8765
```

Attach later and press Enter if the supervisor reports a dead session:

```shell
tmux attach -t colab-opencode-supervisor
```

Runtime paths:

- Optional OpenCode binary: `/root/.opencode/bin/opencode`
- Persistent Drive root: `/content/drive/MyDrive/colab-terminal`
- Persistent project folder: `/content/drive/MyDrive/colab-terminal/projects/<project-name>`
- Recovery notebook: `/content/drive/MyDrive/colab-terminal/colab-terminal.ipynb`
- Runtime state: `/content/colab-terminal-session-state.json`
- Drive state copy: `/content/drive/MyDrive/colab-terminal/sessions/terminal-state.json`
- Backend log: `/content/colab-terminal-ttyd.log` or `/content/colab-terminal-ghosttown.log`
- Backend PID file: `/content/colab-terminal-ttyd.pid` or `/content/colab-terminal-ghosttown.pid`
- Ghost Town shell: `/content/colab-terminal-ghosttown-shell.sh`
- Ghost Town tmux attach command: `tmux attach -t drive-terminal`
- Terminal command mode: `opencode` or `shell`

Requirements:

- The Colab browser page must connect to MCP.
- When Chrome is already running without CDP, the script tries to accept Colab's
  local MCP Connect dialog through visible-browser Hyprland/ydotool automation.
  It opens a fresh Chrome window with the scratch URL, then retries `enter`,
  `tab-enter`, and `tab-tab-enter` unless disabled.
- The Colab notebook execution slot must be free. If a prior cell is stuck,
  interrupt it in the Colab UI with `Ctrl+M`, then `I`, before running setup.
- Opencode still needs provider API keys or provider login/configuration before
  it can complete model-backed tasks.
