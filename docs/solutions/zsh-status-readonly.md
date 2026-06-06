# zsh Read-Only Status Variable

- Problem: [docs/problems/2026-06-06-zsh-status-readonly.md](../problems/2026-06-06-zsh-status-readonly.md)

## What Failed

The supervisor polling command assigned to a zsh read-only parameter:

```bash
status=$(python - <<'PY'
...
PY
)
```

zsh rejected the command with:

```text
zsh:1: read-only variable: status
```

## What Worked

Use a non-reserved variable name:

```bash
state_value=$(python - <<'PY'
...
PY
)
```

## Why It Worked

`status` is reserved by zsh for the previous command exit status. `state_value` is an ordinary variable name, so zsh allows assignment and the loop can poll the supervisor state JSON.

## Commands Run

```bash
for i in {1..60}; do state_value=$(python - <<'PY'
import json
from pathlib import Path
p=Path('/tmp/colab-mcp-opencode-session-state.json')
print(json.loads(p.read_text()).get('status') if p.exists() else 'missing')
PY
); echo "$(date -Iseconds) state=$state_value"; [ "$state_value" = running ] && break; sleep 5; done
cat /tmp/colab-mcp-opencode-session-state.json
ss -ltnp 'sport = :8765' || true
```

Result: the supervisor reached `status=running`, health showed `httpOk=true`, `websocketOk=true`, and Python PID `3202746` listened on `127.0.0.1:8765`.
