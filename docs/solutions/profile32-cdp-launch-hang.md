# Profile 32 CDP Launch Hang Solution

Links back to: [Profile 32 CDP launch hang](../problems/2026-06-07-profile32-cdp-launch-hang.md)

## What Failed

The Drive terminal wizard correctly fell back from the non-primary `Default` Chrome profile to the primary signed-in `Profile 32`, but the controlled Chrome browser did not stay alive long enough to expose CDP on port `9463`.

The copied profile directory contained stale Chrome runtime files:

```text
SingletonCookie
SingletonSocket
SingletonLock
```

The MCP browser connection path also discarded browser launch output, so the user only saw the command pause at:

```text
Connecting Colab MCP browser session...
```

## Alternatives Evaluated

1. Always refresh the copied profile directory.
   - Trade-off: Clears stale locks, but also discards useful copied-profile auth state and slows every launch.
2. Kill stale Chrome and MCP processes before retrying.
   - Trade-off: May unblock the current run, but is user-disruptive and does not fix the next stale copied-profile launch.
3. Add browser launch logs only.
   - Trade-off: Improves evidence, but leaves stale `Singleton*` files in place.
4. Remove stale `Singleton*` files from copied profiles before launch.
   - Trade-off: Targets only temporary copied profiles and leaves the real Chrome profile untouched.
5. Add wizard preflight checks for CDP/process state.
   - Trade-off: Useful follow-up, but it detects the hang later than cleaning the copied-profile launch state.

Selected approach: combine option 4 and option 3.

Confidence: 100% for this local strategy because it only mutates temporary copied Chrome profile directories and adds diagnostics. It does not claim that every Colab login or runtime allocation issue is solved.

## What Worked

- Added copied-profile runtime lock cleanup before reusing a copied Chrome profile.
- Captured controlled Chrome stdout and stderr to a browser launch log.
- Included the browser launch log path and tail in CDP timeout errors.
- Logged controlled-browser navigation exceptions instead of silently returning `False`.

## Why It Worked

Chrome creates `Singleton*` files in the user data directory while running. If a controlled browser launch exits early, those files can remain in the copied profile. Reusing that copied profile can make a later launch fail before CDP opens.

Cleaning only the copied profile is safe because the source Chrome profile under `/home/astra/.config/google-chrome` is never modified. Capturing the browser log gives direct evidence if Chrome still exits for a different reason.

## Commands Run

```bash
sed -n '1,220p' /home/astra/.codex/skills/systematic-debugging/SKILL.md
pwd
git status --short --branch
date -Iseconds
rg -n "_copy_browser_profile|_ensure_controlled_edge|_navigate_controlled_edge|Singleton|browser_profile_copy" src tests scripts
tail -n 40 docs/steps.md
sed -n '3040,3185p' src/colab_mcp/session.py
sed -n '3360,3425p' src/colab_mcp/session.py
sed -n '4485,4535p' src/colab_mcp/session.py
sed -n '180,380p' tests/session_test.py
sed -n '380,520p' tests/session_test.py
sed -n '1,140p' src/colab_mcp/session.py
rg -n "logging|logger|BROWSER_.*LOG|EDGE_CDP_PORT_ENV|BROWSER_.*ENV|_env_bool|def _browser_user_data_dir|BROWSER_PROFILE_COPY_DIR_ENV" src/colab_mcp/session.py
sed -n '2920,2965p' src/colab_mcp/session.py
sed -n '3320,3395p' src/colab_mcp/session.py
sed -n '4535,4615p' src/colab_mcp/session.py
uv run pytest tests/session_test.py::TestControlledEdgeLaunch::test_copy_profile_reuse_removes_stale_runtime_locks tests/session_test.py::TestControlledEdgeLaunch::test_ensure_controlled_edge_timeout_includes_browser_log_tail -q
rg -n "0\\.10\\.1|version =|v0\\.10\\.1|## \\[v0" pyproject.toml uv.lock CHANGELOG.md
sed -n '1,90p' CHANGELOG.md
sed -n '1,80p' pyproject.toml
sed -n '1,40p' uv.lock
uv lock
uv run pytest -q
printf '2\n\n1\n' | uv run colab-drive-terminal --dry-run
uv run python -c "import importlib.metadata; print(importlib.metadata.version('colab-mcp'))"
find /tmp/colab-mcp-drive-terminal-profile-copy-profile-32 -maxdepth 1 -name 'Singleton*' -printf '%f\n'
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome COLAB_MCP_BROWSER_PROFILE='Profile 32' COLAB_MCP_BROWSER_COPY_PROFILE=1 COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-drive-terminal-profile-copy-profile-32 uv run python -c "from colab_mcp import session; print('\n'.join(session._controlled_browser_command('https://example.test', port='9463')))"
find /tmp/colab-mcp-drive-terminal-profile-copy-profile-32 -maxdepth 1 -name 'Singleton*' -printf '%f\n'
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome COLAB_MCP_BROWSER_PROFILE='Profile 32' COLAB_MCP_BROWSER_COPY_PROFILE=1 COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-drive-terminal-profile-copy-profile-32 COLAB_MCP_BROWSER_LAUNCH_LOG=/tmp/colab-mcp-cdp-smoke-9477.log uv run python -c "from colab_mcp import session; session._ensure_controlled_edge('about:blank', port='9477'); print('cdp ok')"
ss -ltnp | rg ':9477\b'
pgrep -af -- '--remote-debugging-port=9477'
tail -n 20 /tmp/colab-mcp-cdp-smoke-9477.log
sed -n '1,80p' /tmp/colab-mcp-cdp-smoke-9477.log
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome COLAB_MCP_BROWSER_PROFILE='Profile 32' COLAB_MCP_BROWSER_COPY_PROFILE=1 COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-drive-terminal-profile-copy-profile-32 COLAB_MCP_BROWSER_LAUNCH_LOG=/tmp/colab-mcp-cdp-smoke-9478.log uv run python -c "from colab_mcp import session; import time; session._ensure_controlled_edge('about:blank', port='9478'); time.sleep(5); print('alive_after_5s', session._cdp_alive('9478'))"
ss -ltnp | rg ':9478\b'
pgrep -af -- '--remote-debugging-port=9478'
find /tmp/colab-mcp-drive-terminal-profile-copy-profile-32 -maxdepth 1 -name 'Singleton*' -printf '%f\n'
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome COLAB_MCP_BROWSER_PROFILE='Profile 32' COLAB_MCP_BROWSER_COPY_PROFILE=1 COLAB_MCP_BROWSER_PROFILE_COPY_DIR=/tmp/colab-mcp-drive-terminal-profile-copy-profile-32 uv run python -c "from colab_mcp import session; session._controlled_browser_command('about:blank', port='9463'); print('profile copy cleaned')"
find /tmp/colab-mcp-drive-terminal-profile-copy-profile-32 -maxdepth 1 -name 'Singleton*' -printf '%f\n'
pgrep -af 'uv run colab-drive-terminal|colab_opencode_localhost.py.*--cdp-port 9463|colab-mcp-drive-terminal-profile-copy-profile-32'
ss -ltnp | rg ':(8768|9463|7686)\b'
find /tmp/colab-mcp-drive-terminal-profile-copy-profile-32 -maxdepth 1 -name 'Singleton*' -printf '%f\n'
```

## Verification

- Focused tests passed: `2 passed in 2.44s`.
- Full suite passed: `93 passed, 1 warning in 8.25s`.
- Dry-run from `/home/astra` still falls back from `Default` to `Profile 32`.
- The real copied Profile 32 directory no longer contains `Singleton*` files after the patched browser command path runs.
- Controlled Chrome CDP launch smoke passed with `cdp ok`.
- Controlled Chrome stayed reachable long enough for bridge automation in a five-second parent-alive smoke: `alive_after_5s True`.
