# Ghost Town Web-Managed Opencode Session

- Date: 2026-06-06
- Problem: `docs/problems/2026-06-06-ghosttown-tmux-session-not-web-managed.md`

## What Failed

The first Ghost Town backend started OpenCode in a detached `tmux` session and then launched `ghosttown -p ... --http --no-auth`. Source inspection showed that Ghost Town web mode uses its own `SessionManager` with `node-pty`, persisted session metadata, and the `SHELL` environment variable for new browser sessions. A detached tmux process would not automatically become the `/new` web terminal session.

## What Worked

The generated setup cell now writes `/content/opencode-ghosttown-shell.sh` and starts Ghost Town with `SHELL=/content/opencode-ghosttown-shell.sh`. When the user opens `/new`, Ghost Town creates a web-managed PTY that runs the wrapper, changes to the configured project directory, and executes `opencode`.

## Why It Worked

Ghost Town's web server creates sessions through `SessionManager.createSession()`, and the PTY process uses `process.env.SHELL` as the default shell. Setting `SHELL` to an executable wrapper aligns OpenCode startup with Ghost Town's actual web session lifecycle and keeps session metadata under `~/.config/ghosttown`, which is symlinked into Google Drive when Drive persistence is mounted.

## Commands Run

```bash
npm view @seflless/ghosttown version description bin --json
npm pack @seflless/ghosttown --silent
tar -xOf /tmp/seflless-ghosttown-1.9.1.tgz package/src/session/session-manager.js | sed -n '1,260p'
tar -xOf /tmp/seflless-ghosttown-1.9.1.tgz package/src/cli.js | rg -n "new|createSession|SessionManager|defaultShell|startProcess|shell|WebSocket|/api|sessions"
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code
for backend in ('ttyd', 'ghosttown'):
    code = setup_cell_code(port=7681, cwd='/content', install_timeout=600, terminal_backend=backend)
    compile(code, f'<{backend}>', 'exec')
    print(backend, len(code), 'compiled')
PY
uv run ruff check .
uv run python -m compileall -f src scripts
uv run pytest -q tests/opencode_setup_cell_test.py
uv run pytest -q
```
