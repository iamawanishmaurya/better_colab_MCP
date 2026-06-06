# Ghost Town Parallel Source Inspection Race

- Timestamp: 2026-06-06T17:01:20+05:30
- Environment: Local workstation shell while unpacking `@seflless/ghosttown` and reading source files from `/tmp/ghosttown-inspect-source-only`.

## Exact Error

```text
sed: can't read /tmp/ghosttown-inspect-source-only/package/src/cli.js: No such file or directory
sed: can't read /tmp/ghosttown-inspect-source-only/package/src/session/session-manager.js: No such file or directory
```

## Reproduction Steps

1. Run unpacking and reading commands in parallel tool calls.
2. The read commands can execute before the unpack command creates `/tmp/ghosttown-inspect-source-only/package`.
3. `sed` fails because the target source files do not exist yet.

## First Hypothesis

The source-inspection commands raced each other. This is the second missing-path failure in the Ghost Town inspection flow, so the retry pattern must stop and be replaced with a single sequential source-inspection strategy.
