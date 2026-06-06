# Ghost Town Packed Help Missing Dependency

- Timestamp: 2026-06-06T16:59:37+05:30
- Environment: Local temp directory created by `npm pack @seflless/ghosttown` on the workstation while inspecting Ghost Town CLI behavior before adding a Colab backend.

## Exact Error

```text
Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@lydell/node-pty' imported from /tmp/tmp.WU8UVFQXaT/package/src/cli.js
```

## Reproduction Steps

1. Pack the package without installing dependencies:
   ```bash
   tmpdir=$(mktemp -d)
   cd "$tmpdir"
   npm pack @seflless/ghosttown
   tar -xf seflless-ghosttown-1.9.1.tgz
   node package/bin/ghosttown.js --help
   ```
2. The command imports `src/cli.js`, which imports runtime dependencies that are not installed by `npm pack`.

## First Hypothesis

The tarball inspection path is unsuitable for running the CLI because package dependencies are absent. Direct source inspection from the unpacked tarball is still valid for flags and command behavior, while actual execution should use `npm install -g @seflless/ghosttown`.
