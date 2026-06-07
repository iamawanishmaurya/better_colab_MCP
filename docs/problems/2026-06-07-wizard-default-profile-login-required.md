# Problem: Wizard Default profile login required

## Exact Error

The wizard launched MCP successfully with Chrome profile `Default`, but the controlled copied browser opened Colab logged out:

```text
uv run colab-drive-terminal
Chrome profiles:
1. Profile 32 - Awanish - cloudboosterawanish@gmail.com primary
2. Default - Your Chrome - canbehumanagain@gmail.com
Select Chrome profile: 2
Workspace modes:
1. Drive workspace recommended
2. Temporary /content workspace
Select workspace mode [1]: 1
Launching Colab terminal:
uv run python scripts/colab_opencode_localhost.py --repo /home/astra/codex/Google-Colab/better_colab_MCP --terminal-backend ghosttown --terminal-command shell --ghosttown-session-mode tmux --ghosttown-tmux-session drive-terminal --browser-copy-profile --browser-profile Default --browser-profile-copy-dir /tmp/colab-mcp-drive-terminal-profile-copy --cdp-port 9463 --local-port 8768 --colab-port 7686 --cwd /content/drive/MyDrive/colab-terminal/projects/project --no-browser-headless --browser-reuse-profile-copy --drive-persistence --require-drive --drive-folder /content/drive/MyDrive/colab-terminal
Connecting Colab MCP browser session...
Connected to Colab MCP. Browser connected=True
RuntimeError: Colab runtime did not connect: {'ok': False, 'steps': [], 'warnings': ['Colab login is required in the dedicated MCP browser before connecting a runtime.'], 'before': {'loginRequired': True, 'localMcpConnected': True, 'hasRuntime': False, 'hasTerminalConnection': True}, 'after': {'loginRequired': True, 'localMcpConnected': True, 'hasRuntime': False, 'hasTerminalConnection': True}, 'browserConnected': True, 'executionBackend': 'colab-browser-cdp', 'status': 'warning'}
```

The full browser diagnostic payload included visible Colab text with `Sign in` and `Connect to a new runtime`, confirming Colab was not authenticated in the copied profile even though MCP connected.

## Reproduction Steps

1. Run:

   ```bash
   cd /home/astra/codex/Google-Colab/better_colab_MCP
   uv run colab-drive-terminal
   ```

2. Select profile `2`, which maps to Chrome profile directory `Default`.
3. Select Drive workspace mode `1`.
4. The wizard launches `scripts/colab_opencode_localhost.py`.
5. MCP connects, but runtime connection fails because Colab reports `loginRequired: True`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Version: `v0.10.0`
- Date: `2026-06-07T12:27:02+05:30`
- Wizard selected profile: `Default`
- Local State metadata: `Default` has account metadata but is not marked `is_consented_primary_account=true`
- Known primary profile shown by wizard: `Profile 32`
- Copied profile dir used by wizard: `/tmp/colab-mcp-drive-terminal-profile-copy`
- CDP port: `9463`
- Local port: `8768`
- Colab port: `7686`

## First Hypothesis

The wizard reused a shared copied profile directory that can preserve an anonymous or wrong-profile Colab state. It also allowed accidental selection of a non-primary Chrome profile even though prior validation showed `Profile 32` is the only profile marked as Chrome's consented primary account. The wizard should isolate copied profile directories by selected source profile and warn or redirect users away from non-primary profiles unless they explicitly confirm.
