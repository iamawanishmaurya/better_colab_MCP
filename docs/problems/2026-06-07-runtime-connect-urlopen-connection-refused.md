# Runtime Connect Urlopen Connection Refused

## Exact Error

```text
Connecting Colab MCP browser session...
Connected to Colab MCP. Browser connected=True
Traceback (most recent call last):
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 557, in <module>
    main()
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 551, in main
    asyncio.run(run(parse_args()))
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 423, in run
    runtime = await connect_runtime(client, args)
  File "/home/astra/codex/Google-Colab/better_colab_MCP/scripts/colab_opencode_localhost.py", line 344, in connect_runtime
    raise RuntimeError(f"Colab runtime did not connect: {payload}")
RuntimeError: Colab runtime did not connect: {'text': '<urlopen error [Errno 111] Connection refused>'}
```

## Reproduction Steps

1. Start the default-profile bridge:

   ```bash
   uv run python scripts/colab_opencode_localhost.py \
     --terminal-backend ghosttown \
     --ghosttown-session-mode tmux \
     --ghosttown-tmux-session opencode \
     --local-port 8768 \
     --colab-port 7685 \
     --setup-timeout 1200 \
     --install-timeout 900 \
     --drive-mount-timeout 180 \
     --no-browser-headless \
     --no-browser-copy-profile \
     --browser-profile Default \
     --cdp-port 9462 \
     --log-file /tmp/colab-mcp-opencode-ghosttown-default-tmux-mcp.log
   ```

2. Approve the visible "Connect to a local Colab MCP server" dialog in Chrome.
3. The launcher prints `Connected to Colab MCP. Browser connected=True`.
4. The launcher fails during `connect_runtime`.

## Environment

- Timestamp: `2026-06-07T07:45:42+05:30`
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Browser profile: real Chrome `Default` profile, no profile copy
- Local proxy target port: `8768`
- Colab terminal backend port: `7685`
- tmux session: `colab-opencode-ghosttown-default-tmux`

## First Hypothesis

The browser approval successfully connected the frontend to the local MCP server, but the runtime-connect follow-up ran through the CDP/proxy helper after the local page/server state had become unavailable or mismatched. The next fix should verify MCP server state after approval and avoid assuming the CDP runtime-connect path is still reachable.
