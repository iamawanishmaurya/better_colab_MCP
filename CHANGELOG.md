# Changelog

## v0.8.0 - 2026-06-07

- Added Ghost Town tmux session mode with `--ghosttown-session-mode tmux` and `--ghosttown-tmux-session`.
- In tmux mode, Ghost Town `/new` browser terminals attach directly to a reusable Colab tmux session running OpenCode, without SSH.
- Passed Ghost Town tmux controls through the localhost bridge and reconnect supervisor.
- Documented the tmux workflow and added generated setup-cell coverage for Ghost Town tmux mode.

## v0.7.0 - 2026-06-06

- Added Drive-backed Opencode persistence by default, creating `/content/drive/MyDrive/opencode`, a persistent project folder, `opencode.ipynb`, recovery script, and Drive-copied session state.
- Symlinked OpenCode state/config/cache paths and Ghost Town config into the Drive folder so chats, project session data, and terminal session metadata can survive Colab runtime loss.
- Added `--terminal-backend ghosttown` to run Opencode through Ghost Town, a Ghostty-powered browser terminal server whose `/new` sessions launch Opencode through a generated shell wrapper.
- Documented the `--no-require-drive` smoke-test path for runtimes where Colab Drive authorization is unavailable.
- Added matching Drive and terminal-backend flags to the localhost bridge and reconnect supervisor.
- Added generated setup-cell tests for ttyd, Ghost Town, and disabled-Drive modes.

## v0.6.1 - 2026-06-06

- Fixed the Opencode localhost WebSocket proxy to preserve ttyd's `tty` subprotocol from the PinchTab/browser client through to the Colab runtime proxy.
- Updated the Opencode supervisor health check to validate the `tty` WebSocket protocol path.
- Added a local regression test for ttyd subprotocol negotiation and proxied WebSocket message forwarding.

## v0.6.0 - 2026-06-06

- Added `scripts/colab_opencode_supervisor.py` to monitor the local Opencode bridge, record session state, detect dead/degraded sessions, and reconnect Colab MCP plus Opencode when the user presses Enter.
- Added health checks for local ttyd HTTP and WebSocket endpoints.
- Documented the supervisor workflow and `/tmp/colab-mcp-opencode-session-state.json` state file.

## v0.5.0 - 2026-06-06

- Added `scripts/colab_opencode_localhost.py` to start Opencode in Colab and expose the `ttyd` PTY at local `http://127.0.0.1:<port>` without SSH.
- Added local HTTP/WebSocket reverse proxying from laptop localhost to Colab's kernel port proxy.
- Added CDP extraction of the Colab runtime proxy cookie, with redacted cookie diagnostics, so server-side localhost proxy requests can authenticate to the Colab port proxy.
- Updated the Opencode setup cell to emit `proxyUrl` and proxy URL errors in `COLAB_OPENCODE_RESULT`.
- Added localhost smoke testing for ttyd HTML and verified WebSocket access at `ws://127.0.0.1:8765/ws`.
- Added `aiohttp` as a runtime dependency for local HTTP/WebSocket proxy support.

## v0.4.0 - 2026-06-06

- Added headless Chrome/CDP auth mode with `COLAB_MCP_BROWSER_HEADLESS`, `COLAB_MCP_BROWSER_COOKIE_FILE`, blank-first launch, and cookie import before Colab navigation.
- Added `COLAB_MCP_BROWSER_COPY_PROFILE` and `COLAB_MCP_BROWSER_PROFILE_COPY_DIR` to clone a locked Chrome profile into a dedicated headless/CDP profile, matching the practical browser-use approach without depending on browser-use at runtime.
- Added redacted cookie diagnostics and `.gitignore` coverage for local cookie/auth artifacts.
- Documented browser-use compatibility and why this fork uses direct CDP for deterministic Colab MCP connection instead of adding browser-use as a required runtime dependency.
- Added visible-browser auto-connect fallback for Colab's local MCP Connect dialog when Chrome is already running without CDP.
- Added guarded Hyprland/ydotool automation that can open the scratch URL in a fresh visible Chrome window, then retry `enter`, `tab-enter`, and `tab-tab-enter` strategies.
- Added CLI/env controls for auto-connect delay, interval, attempts, target window title, and disabling visible automation.
- Made the Colab proxy client reconnectable after frontend WebSocket drops instead of treating the first frontend connection as a one-shot lifetime.

## v0.3.0 - 2026-06-06

- Added `scripts/colab_opencode_web_terminal.py` to install Opencode in Colab and expose it through a `ttyd` browser PTY.
- Added `docs/OPENCODE_COLAB.md` with setup, runtime paths, and recovery notes.
- Documented recovery from stuck notebook-cell execution before running interactive terminal setup.

## v0.2.0 - 2026-06-06

- Added `scripts/colab_cell_terminal.py`, a tmux-friendly shell bridge backed by a reusable Colab code cell over MCP.
- Added `docs/TMUX_CELL_TERMINAL.md` with attach/start instructions and limitations.
- Added bridge startup diagnostics, redacted connection URL output, explicit Chrome new-window opening, and a longer default browser connection timeout.
- Verified live MCP browser connection, `add_code_cell`, and `run_code_cell` against the local Chrome profile.

## v0.1.0 - 2026-06-06

- Rebased local work onto `404F0X/better_colab_MCP` instead of the Google baseline clone.
- Added Chrome/Chromium-compatible controlled browser startup while preserving legacy Edge env aliases.
- Added `COLAB_MCP_BROWSER_COMMAND`, `COLAB_MCP_BROWSER_USER_DATA_DIR`, `COLAB_MCP_BROWSER_PROFILE`, `COLAB_MCP_CONNECTION_TIMEOUT`, and `COLAB_MCP_PRINT_CONNECTION_URL`.
- Added CLI flags for browser command, browser user data directory, browser profile, connection timeout, and stderr URL printing.
- Added `get_connection_info().browser` diagnostics for command, profile, user data directory, CDP port, URL filter, URL printing, and effective timeout.
- Documented the local `nothumanatall` / `Default` Chrome profile workflow.
- Converted the former Chinese README content to English-only documentation.

## 1.0.1+fork.0

- Forked from the static Colab MCP baseline.
- Added runtime file tools: upload/download/stat/list/delete/mkdir and chunked transfer.
- Added batch notebook/cell helpers: upload/download aliases, replace/patch/find/get cell, batch/range/all execution, status, waiting, and output polling.
- Added environment helpers: get, unset, and `.env` loading with redaction.
- Added background job listing/watching and GPU timestamp sampling/monitoring.
- Added browser userscript tools under `colab_ext.*`.
- Added `colabctl` for Edge CDP control, status, connection repair, browser smoke tests, snapshots, and UI clicks.
