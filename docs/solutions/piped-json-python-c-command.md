# Piped JSON Python Command Fix

- Date: 2026-06-06
- Problem: `docs/problems/2026-06-06-piped-json-python-heredoc-collision.md`

## What Failed

The session inspection command piped JSON into `python -` while also using a here-document for the Python source. That made standard input ambiguous and produced invalid Python input.

## What Worked

Using `python -c` kept standard input available for the piped JSON and placed the Python program in the command argument.

## Why It Worked

`python -c` reads code from the command line instead of standard input. The pipe can then deliver only the JSON payload to `json.load(sys.stdin)`.

## Commands Run

```bash
curl -fsS 'http://127.0.0.1:8766/api/sessions' | python -c 'import json,sys; payload=json.load(sys.stdin); [print(session["id"], session["name"], session.get("isRunning")) for session in payload.get("sessions", [])]'
```

## Evidence

```text
41fe23cc-631d-499d-a2de-53ff640d1358 2 True
4781ece2-044d-4866-8182-4808aec389cc 1 False
```
