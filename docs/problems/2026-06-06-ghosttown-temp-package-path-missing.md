# Ghost Town Temp Package Path Missing

- Timestamp: 2026-06-06T17:00:23+05:30
- Environment: Local workstation shell while inspecting the previously unpacked `@seflless/ghosttown` tarball under `/tmp`.

## Exact Error

```text
pkgdir=
rg: /cli.js: No such file or directory (os error 2)
sed: can't read /cli.js: No such file or directory
sed: can't read /session/session-manager.js: No such file or directory
```

## Reproduction Steps

1. Try to rediscover an unpacked npm package path from a prior temporary shell:
   ```bash
   pkgdir=$(find /tmp -maxdepth 2 -path '*/package/src/cli.js' -printf '%h\n' 2>/dev/null | tail -1)
   sed -n '1,260p' "$pkgdir/cli.js"
   ```
2. If the temp directory is gone or not matched by the `find` depth, `pkgdir` is empty and the command tries to read `/cli.js`.

## First Hypothesis

The earlier `mktemp` directory was not reliably discoverable from the follow-up shell. The fix is to unpack the npm package into a known path and inspect files from that stable path.
