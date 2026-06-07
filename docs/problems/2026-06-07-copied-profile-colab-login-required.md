# Copied Profile Colab Login Required

- Date: 2026-06-07
- Area: Live shell-mode runtime connection

## Exact Error

After Chrome relaunched with local-network websocket checks disabled, the MCP browser connection succeeded:

```text
Connected to Colab MCP. Browser connected=True
```

The next step failed while connecting the Colab runtime:

```text
RuntimeError: Colab runtime did not connect: {'ok': False, 'warnings': ['Colab login is required in the dedicated MCP browser before connecting a runtime.'], ...}
```

The live page state included:

```json
{
  "loginRequired": true,
  "localMcpConnected": true,
  "hasNotebook": true,
  "hasRuntime": false
}
```

## Reproduction Steps

1. Stop the controlled Chrome process on CDP port `9463`.
2. Relaunch the shell-mode bridge so Chrome starts with local-network websocket checks disabled.
3. Observe MCP browser attach succeed.
4. Observe runtime connection fail because the controlled copied profile shows `Sign in`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser: Google Chrome `148.0.7778.215`
- Controlled Chrome CDP port: `9463`
- Controlled copied profile path: `/tmp/colab-mcp-opencode-realcopy-profile`
- Requested profile directory: `Default`

## First Hypothesis

The `Default` source profile copied into the controlled browser is not the signed-in Colab profile after relaunch. The launch command should use the Chrome profile directory that belongs to `nothumanatall` / `canbehumanagain`.
