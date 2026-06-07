# Real Default Chrome CDP Blocked

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-real-default-chrome-cdp-blocked.md](../problems/2026-06-07-real-default-chrome-cdp-blocked.md)

## What Failed

Restarting Chrome's real default data directory with remote debugging did not open the CDP port. Chrome printed:

```text
DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.
```

This happened even with `--user-data-dir=/home/astra/.config/google-chrome`, because that path is Chrome's default user data directory.

## What Worked

Using a copied non-default profile directory kept the Colab account signed in and made the browser controllable through CDP:

```bash
uv run python scripts/colab_opencode_localhost.py \
  --terminal-backend ghosttown \
  --ghosttown-session-mode tmux \
  --ghosttown-tmux-session opencode \
  --no-browser-headless \
  --browser-copy-profile \
  --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile \
  --browser-profile Default \
  --cdp-port 9463
```

Live validation later confirmed the copied profile was signed into `canbehumanagain@gmail.com` and CDP-controllable on port `9463`.

## Why It Worked

Current Chrome rejects remote debugging on the real default user data directory, but allows remote debugging on a non-default user data directory. Copying the selected profile preserves the signed-in Colab state without attaching CDP to the protected default profile path.

## Commands Run

```bash
setsid google-chrome-stable --remote-debugging-address=127.0.0.1 --remote-debugging-port=9463 --user-data-dir=/home/astra/.config/google-chrome --profile-directory=Default --no-first-run --new-window https://colab.research.google.com/notebooks/empty.ipynb
curl http://127.0.0.1:9463/json/version
rm -rf /tmp/colab-mcp-opencode-realcopy-profile
tmux new-session -d -s colab-opencode-ghosttown-cdp-tmux 'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_opencode_localhost.py --terminal-backend ghosttown --ghosttown-session-mode tmux --ghosttown-tmux-session opencode --local-port 8768 --colab-port 7685 --setup-timeout 1200 --install-timeout 900 --drive-mount-timeout 240 --no-browser-headless --browser-copy-profile --browser-profile-copy-dir /tmp/colab-mcp-opencode-realcopy-profile --browser-profile Default --cdp-port 9463 --log-file /tmp/colab-mcp-opencode-realcopy-tmux-mcp.log > /tmp/colab-mcp-opencode-realcopy-tmux.log 2>&1'
```
