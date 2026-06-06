# Headless Existing Profile Locked

## Exact Error

Launching a second headless Chrome against `/home/astra/.config/google-chrome` did not open the configured CDP port:

```text
curl: (7) Failed to connect to 127.0.0.1 port 9456
```

The profile was already locked by a visible Chrome process:

```text
/home/astra/.config/google-chrome/SingletonLock -> Astra-2648973
/home/astra/.config/google-chrome/SingletonSocket -> /tmp/com.google.Chrome.x9r8yo/SingletonSocket
```

The attempted subprocess produced a defunct Chrome child instead of a browser listening on CDP port `9456`.

## Reproduction Steps

1. Started a 3-cycle live test with:

```bash
COLAB_MCP_BROWSER_COMMAND=google-chrome-stable \
COLAB_MCP_BROWSER_HEADLESS=1 \
COLAB_MCP_BROWSER_USER_DATA_DIR=/home/astra/.config/google-chrome \
COLAB_MCP_BROWSER_PROFILE=Default \
COLAB_MCP_EDGE_CDP_PORT=9456 \
COLAB_MCP_CONNECTION_TIMEOUT=240 \
uv run python - <<'PY'
# started three MCP connection cycles through FastMCP Client
PY
```

2. Checked CDP:

```bash
ss -ltnp | rg ':9456'
curl -sS http://127.0.0.1:9456/json/version
```

3. Checked Chrome process and profile-lock state:

```bash
ps -ef | rg '9456|headless|google-chrome|chrome'
ls -la /home/astra/.config/google-chrome | rg 'Singleton|Lock|Default'
```

4. Stopped only the blocked test `timeout`, `uv run python`, and `uv run colab-mcp` processes.

## Environment

- Repo: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- Browser: `google-chrome-stable`
- Intended CDP port: `9456`
- Chrome user data dir: `/home/astra/.config/google-chrome`
- Chrome profile: `Default`
- Profile metadata: `canbehumanagain@gmail.com` / `nothumanatall`

## First Hypothesis

Chrome will not start a second headless instance against a locked real profile. For an already-running profile, the reliable path is to attach to the existing browser through CDP, which requires launching the visible browser with `--remote-debugging-port`, or to use a copied/dedicated profile or cookie file for a separate headless browser.
