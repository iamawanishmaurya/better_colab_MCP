# Rg Pattern Parsed As Flag

- Date: 2026-06-07
- Area: Local source search

## Exact Error

```text
rg: unrecognized flag --ghosttown-session-mode|--terminal-backend|--help|terminal-command|parse_args|colab_opencode_localhost
```

## Reproduction Steps

1. Run `rg` with a search pattern that starts with `--`:

   ```bash
   rg -n "--ghosttown-session-mode|--terminal-backend|--help|terminal-command|parse_args|colab_opencode_localhost" tests -S
   ```

2. Observe that `rg` treats the pattern as an option flag.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Shell: `zsh`
- Tool: `rg`

## First Hypothesis

The pattern begins with `--`, so ripgrep parses it as a long option. Use `rg -- <pattern>` or rearrange the search expression.
