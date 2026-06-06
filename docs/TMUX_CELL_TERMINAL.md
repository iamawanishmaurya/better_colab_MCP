# Tmux Cell Terminal

This helper opens an interactive local shell prompt in tmux while executing each
command through a reusable Colab code cell over MCP.

It is useful when Chrome is already running without CDP. The bridge starts a
client-managed MCP server, opens the scratch URL in the existing Chrome profile,
waits for Colab frontend MCP connection, creates a code cell, and reuses that
cell for commands.

Start it:

```shell
tmux new-session -s colab-cell-terminal \
  'cd /home/astra/codex/Google-Colab/better_colab_MCP && uv run python scripts/colab_cell_terminal.py'
```

Attach later:

```shell
tmux attach -t colab-cell-terminal
```

Default browser settings:

- Browser command: `google-chrome-stable`
- User data directory: `/home/astra/.config/google-chrome`
- Profile directory: `Default`
- Browser open mode: `new-window`
- Connection timeout: `600` seconds
- Initial Colab working directory: `/content`

Useful startup flags:

- `--print-url`: print the full scratch URL if Chrome does not navigate.
- `--browser-open-mode new-tab`: open in a tab instead of a new window.
- `--connection-timeout 900`: wait longer for slow Colab browser handoffs.

Limitations:

- This is a shell bridge through notebook cell execution, not a real PTY.
- Full-screen interactive programs are not supported.
- Long-running work should still use MCP background-command tools when a
  Colab terminal runtime connection is available.
