# Generated Setup Cell Compile Verification Command Fixes

Problem files:

- [../problems/2026-06-07-generated-cell-compile-pythonpath.md](../problems/2026-06-07-generated-cell-compile-pythonpath.md)
- [../problems/2026-06-07-generated-cell-compile-wrong-helper-argument.md](../problems/2026-06-07-generated-cell-compile-wrong-helper-argument.md)

## What Failed

The ad hoc generated setup-cell compile verification first imported the script as a package module without adding `scripts/` to `PYTHONPATH`, which prevented sibling script imports from resolving. The next clean retry used a stale `auth_token` keyword that is not part of the current `setup_cell_code()` signature.

## What Worked

The successful command used `PYTHONPATH=scripts`, imported the helper as a script module, and passed the actual required helper arguments:

```bash
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code

base = {"port": 7683, "cwd": "/content/opencode-project", "install_timeout": 900, "require_drive": False}
cases = [
    ("ttyd", {"terminal_backend": "ttyd"}),
    ("ghosttown-direct", {"terminal_backend": "ghosttown"}),
    ("ghosttown-tmux", {"terminal_backend": "ghosttown", "ghosttown_session_mode": "tmux"}),
]

for name, kwargs in cases:
    code = setup_cell_code(**base, **kwargs)
    compile(code, f"<{name}>", "exec")
    print(f"{name}: compiled")
PY
```

Output:

```text
ttyd: compiled
ghosttown-direct: compiled
ghosttown-tmux: compiled
```

## Why It Worked

The scripts use top-level sibling imports when run as scripts, so `PYTHONPATH=scripts` matches the expected import environment. The helper signature requires `port`, `cwd`, and `install_timeout`, so passing those actual arguments exercises the generator instead of failing before compilation.

## Commands Run

```bash
rg -n "^def setup_cell_code|token" scripts/colab_opencode_web_terminal.py | head -n 40
sed -n '83,110p' scripts/colab_opencode_web_terminal.py
PYTHONPATH=scripts uv run python - <<'PY'
from colab_opencode_web_terminal import setup_cell_code

base = {"port": 7683, "cwd": "/content/opencode-project", "install_timeout": 900, "require_drive": False}
cases = [
    ("ttyd", {"terminal_backend": "ttyd"}),
    ("ghosttown-direct", {"terminal_backend": "ghosttown"}),
    ("ghosttown-tmux", {"terminal_backend": "ghosttown", "ghosttown_session_mode": "tmux"}),
]

for name, kwargs in cases:
    code = setup_cell_code(**base, **kwargs)
    compile(code, f"<{name}>", "exec")
    print(f"{name}: compiled")
PY
```
