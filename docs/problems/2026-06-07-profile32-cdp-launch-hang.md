# Profile 32 CDP Launch Hang

## Exact Error

The interactive wizard selected a signed-in fallback profile and then paused at:

```text
Connecting Colab MCP browser session...
```

The command being launched was:

```text
uv run python scripts/colab_opencode_localhost.py --repo /home/astra/codex/Google-Colab/better_colab_MCP --terminal-backend ghosttown --terminal-command shell --ghosttown-session-mode tmux --ghosttown-tmux-session drive-terminal --browser-copy-profile --browser-profile Profile 32 --browser-profile-copy-dir /tmp/colab-mcp-drive-terminal-profile-copy-profile-32 --cdp-port 9463 --local-port 8768 --colab-port 7686 --cwd /content/drive/MyDrive/colab-terminal/projects/project --no-browser-headless --browser-reuse-profile-copy --drive-persistence --require-drive --drive-folder /content/drive/MyDrive/colab-terminal
```

Observed diagnostics:

```text
ss -ltnp | rg ':(8768|9463|7686)\b'
```

returned no listener for `9463`, `8768`, or `7686`.

The copied profile directory existed, but contained Chrome runtime lock files:

```text
/tmp/colab-mcp-drive-terminal-profile-copy-profile-32/SingletonCookie
/tmp/colab-mcp-drive-terminal-profile-copy-profile-32/SingletonLock -> Astra-884652
/tmp/colab-mcp-drive-terminal-profile-copy-profile-32/SingletonSocket -> /tmp/com.google.Chrome.rmgL1m/SingletonSocket
```

No matching Chrome process with `--remote-debugging-port=9463` was running.

## Reproduction Steps

1. Run `uv run colab-drive-terminal` from `/home/astra`.
2. Select Chrome profile `2` (`Default`).
3. Press Enter at the non-primary profile warning so the wizard falls back to `Profile 32`.
4. Select Drive workspace mode `1`.
5. Observe the command pause at `Connecting Colab MCP browser session...`.

## Environment

- Date: 2026-06-07
- Host: Linux user environment at `/home/astra`
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Chrome: `google-chrome-stable` version `148.0.7778.215`
- Browser copy dir: `/tmp/colab-mcp-drive-terminal-profile-copy-profile-32`
- CDP port: `9463`

## First Hypothesis

The copied Chrome profile is being reused with stale `Singleton*` runtime lock files from a previous failed Chrome launch. Chrome exits before opening CDP on port `9463`, and the MCP browser navigation path hides the launch failure behind a generic wait at `Connecting Colab MCP browser session...`.
