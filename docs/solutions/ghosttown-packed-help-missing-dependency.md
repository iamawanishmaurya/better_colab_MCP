# Ghost Town Packed Help Missing Dependency

- Problem: [docs/problems/2026-06-06-ghosttown-packed-help-missing-dependency.md](../problems/2026-06-06-ghosttown-packed-help-missing-dependency.md)

## What Failed

Running the CLI help from an unpacked `npm pack` tarball failed because runtime dependencies were not installed:

```bash
node package/bin/ghosttown.js --help
```

Error:

```text
Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@lydell/node-pty' imported from /tmp/tmp.WU8UVFQXaT/package/src/cli.js
```

## What Worked

Read source files directly from the npm tarball:

```bash
npm pack @seflless/ghosttown
tar -O -xf seflless-ghosttown-1.9.1.tgz package/src/cli.js
tar -O -xf seflless-ghosttown-1.9.1.tgz package/src/session/session-manager.js
```

## Why It Worked

Source inspection does not execute `src/cli.js`, so Node does not need to resolve `@lydell/node-pty`. It still uses the exact published package source, which is enough to confirm CLI flags and startup behavior.

## Commands Run

```bash
npm view @seflless/ghosttown version bin scripts description --json
npm view @wterm/ghostty version description --json
npm view @seflless/ghosttown dist.tarball --json
npm pack @seflless/ghosttown
tar -O -xf seflless-ghosttown-1.9.1.tgz package/src/cli.js
tar -O -xf seflless-ghosttown-1.9.1.tgz package/src/session/session-manager.js
```

Result: Ghost Town `1.9.1` provides `ghosttown`, `gt`, and `ght`; server mode supports `-p/--port`, `--http`, and `--no-auth`; command mode creates and attaches a tmux session, so Colab should start Opencode with detached `tmux` and run Ghost Town as the web server.
