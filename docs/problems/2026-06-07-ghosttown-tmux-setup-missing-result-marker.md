# Ghost Town tmux Startup Missing Setup Result Marker

## Exact Error

```text
Connecting Colab MCP browser session...
Connected to Colab MCP. Browser connected=True
Runtime status: {"after": {"hasKernel": true, "hasNotebook": true, "hasRuntime": true, "hasTerminalConnection": true, "href": "https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=<redacted>&mcpProxyPort=<redacted>", "localMcpConnected": true, "loginRequired": false, "ready": "complete", ...}}

Traceback (most recent call last):
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 557, in <module>
    main()
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 551, in main
    asyncio.run(run(parse_args()))
  File "/usr/lib/python3.13/asyncio/runners.py", line 195, in run
    return runner.run(main)
  File "/usr/lib/python3.13/asyncio/runners.py", line 118, in run
    return self._loop.run_until_complete(task)
  File "/usr/lib/python3.13/asyncio/base_events.py", line 725, in run_until_complete
    return future.result()
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 425, in run
    setup = await setup_opencode(client, args)
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 383, in setup_opencode
    result = parse_setup_result(output)
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 80, in parse_setup_result
    raise RuntimeError("Opencode setup did not emit COLAB_OPENCODE_RESULT.")
RuntimeError: Opencode setup did not emit COLAB_OPENCODE_RESULT.
```

## Reproduction Steps

1. From `/home/astra/codex/Google-Colab/better_colab_MCP`, start the tmux-mode bridge:

   ```bash
   uv run python scripts/colab_opencode_localhost.py \
     --terminal-backend ghosttown \
     --ghosttown-session-mode tmux \
     --ghosttown-tmux-session opencode \
     --local-port 8767 \
     --colab-port 7684 \
     --setup-timeout 1200 \
     --install-timeout 900 \
     --drive-mount-timeout 180 \
     --log-file /tmp/colab-mcp-opencode-ghosttown-tmux-start-mcp.log
   ```

2. The browser connects to Colab MCP and runtime status shows `loginRequired: false`.
3. The setup-cell result parser fails because output does not contain `COLAB_OPENCODE_RESULT=`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- tmux session: `colab-opencode-ghosttown-tmux-start`
- Local port: `8767`
- Colab port: `7684`
- CDP port: `9458`
- Date: `2026-06-07`

## First Hypothesis

The setup cell either returned truncated/hidden output, failed before printing the marker, or the active Colab runtime already had state that prevented the setup code from reaching its final result print.
