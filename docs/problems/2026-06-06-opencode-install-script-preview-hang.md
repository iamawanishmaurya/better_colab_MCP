# Opencode install script preview hang

- Timestamp: 2026-06-06T13:59:55+05:30
- Problem slug: opencode-install-script-preview-hang

## Exact Error

The Colab-backed tmux cell terminal accepted this command but did not return output or a prompt within roughly 20 seconds:

```sh
curl -fsSL https://opencode.ai/install | sed -n '1,120p'
```

The captured pane remained at:

```text
colab:/content$ curl -fsSL https://opencode.ai/install | sed -n '1,120p'
```

## Reproduction Steps

1. Attach to the existing bridge:

   ```sh
   tmux attach -t colab-cell-terminal
   ```

2. Run:

   ```sh
   curl -fsSL https://opencode.ai/install | sed -n '1,120p'
   ```

3. Observe that no output or next prompt appears within the wait window.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- tmux session: `colab-cell-terminal`
- Bridge: `scripts/colab_cell_terminal.py`
- Backing Colab cell: `teLJcDU6_yFf`
- Initial Colab working directory: `/content`
- Browser profile: existing Chrome `Default`

## First Hypothesis

The notebook-cell bridge is waiting for the Colab cell execution to complete. The likely causes are a network wait from the Colab runtime to `opencode.ai`, a curl TLS/DNS delay, or the bridge command wrapper not surfacing partial output until subprocess completion.
