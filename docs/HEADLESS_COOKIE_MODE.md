# Headless Cookie Mode

Headless cookie mode starts a controlled Chrome session through CDP, imports a local browser cookie export, then navigates to Colab and calls Colab's frontend MCP service directly. This avoids the manual local MCP Connect button when CDP is available.

Do not commit cookie exports. Google cookies are live account secrets.

## Recommended Order

1. Use an existing logged-in Chrome profile with CDP when possible.
2. Use copied-profile headless mode when the real Chrome profile is already open and locked.
3. Use headless cookie mode for a dedicated, non-visible Colab session.
4. Use visible key automation only as a fallback when CDP is unavailable.

## Environment

```bash
export COLAB_MCP_BROWSER_COMMAND=google-chrome-stable
export COLAB_MCP_BROWSER_HEADLESS=1
export COLAB_MCP_BROWSER_COOKIE_FILE="$HOME/.config/colab-mcp/colab-cookies.json"
export COLAB_MCP_BROWSER_USER_DATA_DIR="$HOME/.cache/colab-mcp/headless-colab-profile"
export COLAB_MCP_BROWSER_PROFILE=Default
export COLAB_MCP_EDGE_CDP_PORT=9444
export COLAB_MCP_CONNECTION_TIMEOUT=240
```

Then start the server:

```bash
uv run colab-mcp
```

From the MCP client, call:

```text
open_colab_browser_connection()
get_connection_info()
```

If the browser connection succeeds, continue with runtime work:

```text
connect_runtime(waitSeconds=180)
```

## Copied Profile Mode

Use this when the real Chrome profile is already open in visible Chrome. Chrome profile lock files prevent a second headless browser from using the same user data directory directly, so this mode clones the selected profile into a dedicated headless directory and launches Chrome from the clone.

```bash
export COLAB_MCP_BROWSER_COMMAND=google-chrome-stable
export COLAB_MCP_BROWSER_HEADLESS=1
export COLAB_MCP_BROWSER_USER_DATA_DIR="$HOME/.config/google-chrome"
export COLAB_MCP_BROWSER_PROFILE=Default
export COLAB_MCP_BROWSER_COPY_PROFILE=1
export COLAB_MCP_BROWSER_PROFILE_COPY_DIR="$HOME/.cache/colab-mcp/nothumanatall-profile-copy"
export COLAB_MCP_EDGE_CDP_PORT=9444
export COLAB_MCP_CONNECTION_TIMEOUT=240
```

The copy process includes `Local State` and the selected profile directory, and excludes Chrome lock files and large cache folders. This is the closest direct-CDP equivalent to browser-use's temporary profile copy behavior.

## Cookie File Format

The cookie file can be either a JSON list or an object with a `cookies` list. Common browser-export fields are supported:

```json
[
  {
    "domain": ".google.com",
    "expirationDate": 1814601961.536875,
    "httpOnly": true,
    "name": "SID",
    "path": "/",
    "sameSite": "no_restriction",
    "secure": true,
    "value": "<secret>"
  }
]
```

Runtime diagnostics report cookie count, domains, and names only. Cookie values are never printed by this project.

## How It Connects

The controlled browser starts on `about:blank` when `COLAB_MCP_BROWSER_COOKIE_FILE` is set. The server then:

1. Enables CDP Network control.
2. Applies cookies with `Network.setCookie`.
3. Navigates to the Colab scratch notebook URL.
4. Sets `sessionStorage.mcp_proxy_token` and `sessionStorage.mcp_proxy_port`.
5. Calls `window.colab.global.notebook.localColabMcpService.connect()`.

This is the same browser-side connection path used by the existing CDP-controlled tools, but with headless launch and cookie import before the first Colab navigation.

## Browser-Use Compatibility

browser-use supports the same primitives this project needs: `user_data_dir`, `profile_directory`, `storage_state`, and CDP attachment. The implementation here uses direct CDP instead of adding browser-use as a required dependency because the MCP server already has deterministic CDP code and does not need an LLM browser agent to click the Colab dialog.

If you want browser-use to control the same session, point browser-use at the same running CDP port instead of copying a locked Chrome profile.

## Failure Notes

- Headless Google sessions can still require reauthentication. If `get_connection_info()` shows the browser connected but runtime tools report login required, refresh the cookie export or use the logged-in Chrome profile path.
- Cookie files may expire or be revoked by Google. Treat connection failures after a previously working setup as an auth refresh issue first.
- Do not run multiple Chrome instances against the same real Chrome profile. Use the dedicated headless user data directory above or connect to an already-running browser through CDP.
