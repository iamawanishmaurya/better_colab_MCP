# Preserve Signed Copied Profile

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-copied-profile-colab-login-required.md](../problems/2026-06-07-copied-profile-colab-login-required.md)

## What Failed

Relaunching with `--browser-copy-profile` deleted and recopied the controlled browser profile. That fixed Chrome flags, but it also discarded any sign-in state created inside the controlled copied profile.

## What Worked

The profile-copy path now reuses an existing copied profile by default when the requested profile directory already exists. The bridge exposes:

```bash
--browser-reuse-profile-copy
--no-browser-reuse-profile-copy
```

and the environment variable:

```bash
COLAB_MCP_BROWSER_REUSE_PROFILE_COPY=0
```

to force a fresh recopy.

## Why It Worked

The controlled copied profile is the right place to keep a dedicated Colab MCP login. Preserving it across reconnects allows one manual or automated sign-in to survive Chrome restarts and new launch flags.

## Commands Run

```bash
uv run python - <<'PY'
# Read Chrome Local State profile metadata without reading cookie values.
PY
uv run python scripts/colab_opencode_localhost.py --help | rg -n -- '--browser-(copy-profile|profile|user-data-dir|profile-copy-dir)|--cdp-port'
uv run pytest tests/session_test.py::TestControlledEdgeLaunch tests/session_test.py::TestCheckSessionProxyToolFn tests/session_test.py::TestConnectColabTab tests/websocket_server_test.py::test_successful_ipv6_loopback_connection tests/opencode_setup_cell_test.py -q
```
