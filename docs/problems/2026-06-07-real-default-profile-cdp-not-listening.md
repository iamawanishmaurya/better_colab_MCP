# Real Default Profile CDP Not Listening

- Date: 2026-06-07
- Area: Controlled Chrome profile selection

## Exact Error

Launching Chrome directly against `/home/astra/.config/google-chrome` with:

```text
--remote-debugging-port=9463
--user-data-dir=/home/astra/.config/google-chrome
--profile-directory=Default
```

started Chrome processes, but CDP requests failed:

```text
urllib.error.URLError: <urlopen error [Errno 111] Connection refused>
```

`ss` did not show a listener on `127.0.0.1:9463`, even though Chrome process arguments included `--remote-debugging-port=9463`.

## Reproduction Steps

1. Stop the copied-profile controlled Chrome process.
2. Start the shell-mode bridge with `--browser-user-data-dir /home/astra/.config/google-chrome --browser-profile Default --no-browser-copy-profile --cdp-port 9463`.
3. Poll `http://127.0.0.1:9463/json/list`.
4. Observe connection refused while Chrome processes are running.

## Environment

- Browser: Google Chrome `148.0.7778.215`
- Real profile path: `/home/astra/.config/google-chrome`
- Profile directory: `Default`
- Requested CDP port: `9463`

## First Hypothesis

Chrome's current remote-debugging restrictions make the real default user-data directory unreliable for CDP control. A dedicated copied user-data directory remains the safer controlled-browser path.
