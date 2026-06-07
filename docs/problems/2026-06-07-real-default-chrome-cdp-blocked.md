# Real Default Chrome CDP Blocked

## Exact Error

```text
DevTools remote debugging requires a non-default data directory. Specify this using --user-data-dir.
curl: (7) Failed to connect to 127.0.0.1 port 9463 after 0 ms: Could not connect to server
```

## Reproduction Steps

1. Terminate the existing real Chrome `Default` profile process.
2. Launch Chrome with the real profile and a CDP port:

   ```bash
   google-chrome-stable \
     --remote-debugging-address=127.0.0.1 \
     --remote-debugging-port=9463 \
     --user-data-dir=/home/astra/.config/google-chrome \
     --profile-directory=Default \
     --no-first-run \
     --new-window \
     https://colab.research.google.com/notebooks/empty.ipynb
   ```

3. Check `http://127.0.0.1:9463/json/version`.

## Environment

- Timestamp: `2026-06-07T08:00:55+05:30`
- Chrome binary: `google-chrome-stable`
- User data dir: `/home/astra/.config/google-chrome`
- Profile directory: `Default`
- Requested CDP port: `9463`
- Log file: `/tmp/colab-real-default-cdp.log`

## First Hypothesis

Current Chrome blocks remote debugging for the default browser data directory. The next strategy must use a non-default user-data directory that is still signed into Colab, such as a fresh copied profile created after cleanly closing Chrome, or a visible CDP profile signed in through the normal Google flow.
