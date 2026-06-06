# Solution: Chrome CDP timeout with Default profile

## Linked problem

- [Problem: Chrome CDP timeout with Default profile](../problems/2026-06-06-chrome-cdp-timeout-default-profile.md)

## What failed

Launching `google-chrome-stable` with remote debugging against `/home/astra/.config/google-chrome` and profile `Default` did not expose CDP on port `9333`.

## What worked

Diagnostic commands confirmed the cause:

- Chrome was already running from `/home/astra/.config/google-chrome`.
- The profile lock files pointed at the existing Chrome process.
- A manual launch printed `Opening in existing browser session.`
- No process was listening on `9333`.

## Why it worked

Chrome forwards commands to the existing profile owner when the same user data directory is already running. The existing browser process was not started with `--remote-debugging-port=9333`, so the new remote-debugging flags were ignored.

## Commands run

```shell
ps -ef | rg 'chrome|chromium|msedge|remote-debugging|google-chrome' || true
ss -ltnp | rg ':9222|:9333|:9444|:9872|chrome|chrom' || true
find /home/astra/.config/google-chrome -maxdepth 1 \( -name 'SingletonLock' -o -name 'SingletonSocket' -o -name 'SingletonCookie' \) -ls 2>/dev/null || true
google-chrome-stable --remote-debugging-address=127.0.0.1 --remote-debugging-port=9333 --user-data-dir=/home/astra/.config/google-chrome --no-first-run --new-window --profile-directory=Default 'about:blank'
```

## Result

The requested profile cannot be converted into a CDP-controlled browser non-destructively while it is already running without remote debugging. A safe live test must either use an already-authorized debugger endpoint, a dedicated debug browser profile, or ask the user to close/relaunch the existing Chrome profile with remote debugging enabled.
