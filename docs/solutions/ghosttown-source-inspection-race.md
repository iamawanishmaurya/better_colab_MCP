# Ghost Town Source Inspection Race

- Problems:
  - [docs/problems/2026-06-06-ghosttown-temp-package-path-missing.md](../problems/2026-06-06-ghosttown-temp-package-path-missing.md)
  - [docs/problems/2026-06-06-ghosttown-parallel-source-inspection-race.md](../problems/2026-06-06-ghosttown-parallel-source-inspection-race.md)

## What Failed

Two source-inspection attempts used paths that were not guaranteed to exist:

```bash
pkgdir=$(find /tmp -maxdepth 2 -path '*/package/src/cli.js' -printf '%h\n' 2>/dev/null | tail -1)
sed -n '1,260p' "$pkgdir/cli.js"
```

and parallel unpack/read commands against:

```text
/tmp/ghosttown-inspect-source-only/package/src/cli.js
```

Both failed with missing source file paths.

## Options Evaluated

1. Reuse the previous temp directory.
   - Trade-off: fastest when it exists, but unreliable because temp paths are not stable across shell commands.
2. Run `npm install -g @seflless/ghosttown` locally and call `ghosttown --help`.
   - Trade-off: verifies executable behavior, but mutates the workstation global npm state just for inspection.
3. Use `npm pack` and `tar -O` in one sequential shell command.
   - Trade-off: avoids dependency install and avoids temp path races, while still reading the exact published package source.
4. Clone the upstream source repository.
   - Trade-off: useful for deeper debugging, but unnecessary because npm tarball source is enough for CLI flags.
5. Rely only on public docs.
   - Trade-off: low effort, but misses implementation details needed for non-interactive Colab startup.

## What Worked

Option 3 is the selected path: unpack/read from the npm tarball in one sequential command and avoid parallel readers.

## Why It Worked

`tar -O` streams the requested file contents directly from the package archive, so there is no follow-up path to rediscover and no race between unpacking and reading.

## Commands Run

```bash
npm pack @seflless/ghosttown
tar -O -xf seflless-ghosttown-1.9.1.tgz package/src/cli.js
tar -O -xf seflless-ghosttown-1.9.1.tgz package/src/session/session-manager.js
```
