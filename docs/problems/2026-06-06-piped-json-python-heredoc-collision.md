# Piped JSON Python Heredoc Collision

- Date: 2026-06-06
- Area: Live Ghost Town browser verification

## Exact Error

```text
  File "<stdin>", line 1
    {"sessions":[{"name":"2","stableId":"41fe23cc","id":"41fe23cc-631d-499d-a2de-53ff640d1358","lastActivity":1780746911975,"attached":false,"isRunning":true,"connectionCount":0},{"name":"1","stableId":"4781ece2","id":"4781ece2-044d-4866-8182-4808aec389cc","lastActivity":1780746875153,"attached":false,"isRunning":false,"connectionCount":0}]}import json, sys
                                                                                                                                                                                                                                                                                                                                                       ^^^^^^
SyntaxError: invalid syntax
```

## Reproduction Steps

1. Run:

   ```bash
   curl -fsS 'http://127.0.0.1:8766/api/sessions' | python - <<'PY'
   import json, sys
   payload=json.load(sys.stdin)
   for session in payload.get('sessions', []):
       print(session['id'], session['name'], session.get('isRunning'))
   PY
   ```

2. Observe Python receiving the piped JSON and inline script content in an invalid way.

## Environment

- Host: Linux workstation
- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Local Ghost Town proxy: `http://127.0.0.1:8766`
- Shell: `zsh`
- Python: system Python invoked through `python`

## First Hypothesis

The shell command incorrectly combined a pipe with a Python here-document. Use `python -c` for the program and keep standard input reserved for the piped JSON.
