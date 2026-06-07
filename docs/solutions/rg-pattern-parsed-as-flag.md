# Rg Pattern Parsed As Flag

- Date: 2026-06-07
- Problem: [../problems/2026-06-07-rg-pattern-parsed-as-flag.md](../problems/2026-06-07-rg-pattern-parsed-as-flag.md)

## What Failed

`rg` treated a pattern beginning with `--ghosttown-session-mode` as a command-line option instead of a regex pattern.

## What Worked

Use the `--` separator before option-looking patterns, or use a pattern that does not start with `--`.

## Why It Worked

The `--` separator tells `rg` that subsequent arguments are positional values, not options.

## Commands Run

```bash
rg -n -- "--ghosttown-session-mode|--terminal-backend|--help|terminal-command|parse_args|colab_opencode_localhost" tests -S
```
