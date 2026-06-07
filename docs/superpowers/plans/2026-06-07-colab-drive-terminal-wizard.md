# Colab Drive Terminal Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive `colab-drive-terminal` CLI that selects a signed-in Chrome profile, connects Colab MCP, opens a native Ubuntu shell, and keeps project/config/session files safe in Google Drive by default.

**Architecture:** Keep the existing Colab bridge scripts as the execution backend. Add a focused packaged wizard module for Chrome profile discovery, workspace selection, and command construction; update the generated Colab setup cell so shell mode and Drive-first persistence are the true defaults.

**Tech Stack:** Python 3.13, argparse, dataclasses, JSON Chrome `Local State`, existing FastMCP bridge, Ghost Town/ttyd terminal backends, pytest, uv.

---

## File Structure

- Modify `scripts/colab_opencode_web_terminal.py`: update defaults from OpenCode-first to terminal-first; add generic Drive/XDG persistence; make OpenCode installation optional and only automatic for OpenCode mode.
- Modify `scripts/colab_opencode_localhost.py`: update labels/help text and pass new setup options.
- Create `src/colab_mcp/drive_terminal_wizard.py`: interactive wizard, Chrome profile discovery, workspace choice handling, command construction, and subprocess execution.
- Create `scripts/colab_drive_terminal.py`: thin local script wrapper for the packaged wizard.
- Modify `pyproject.toml`: add `colab-drive-terminal` console script and bump version to `0.10.0`.
- Modify `uv.lock`: refresh package version.
- Modify `docs/OPENCODE_COLAB.md`: document the new terminal-first workflow.
- Modify `CHANGELOG.md`: add `v0.10.0`.
- Create `tests/drive_terminal_wizard_test.py`: unit tests for profile parsing, workspace choices, and command construction.
- Modify `tests/opencode_setup_cell_test.py`: update setup-cell expectations for shell defaults, XDG persistence, temporary mode, and optional OpenCode mode.
- Modify `docs/steps.md`: log each implementation and validation step immediately.

## Task 1: Generated Colab Setup Defaults And Persistence

**Files:**
- Modify: `scripts/colab_opencode_web_terminal.py`
- Modify: `scripts/colab_opencode_localhost.py`
- Modify: `tests/opencode_setup_cell_test.py`

- [x] **Step 1: Write failing tests for terminal-first defaults**

Add these tests to `tests/opencode_setup_cell_test.py`:

```python
def test_setup_cell_defaults_to_shell_and_colab_terminal_drive_root():
    code = setup_cell_code(port=7681, cwd="/content", install_timeout=600)

    compile(code, "<colab-terminal-default-setup>", "exec")
    assert "TERMINAL_COMMAND = 'shell'" in code
    assert "DRIVE_FOLDER = '/content/drive/MyDrive/colab-terminal'" in code
    assert "NOTEBOOK_NAME = 'colab-terminal.ipynb'" in code
    assert "COLAB_TERMINAL_RESULT " in code
    assert "\ninstall_opencode()\nrun(\"opencode --version\", timeout=60)" not in code


def test_setup_cell_persists_xdg_config_and_share_to_drive():
    code = setup_cell_code(port=7681, cwd="/content", install_timeout=600)

    compile(code, "<colab-terminal-xdg-setup>", "exec")
    assert 'ensure_persistent_dir("~/.config", drive_root / "home" / ".config")' in code
    assert 'ensure_persistent_dir("~/.local/share", drive_root / "home" / ".local" / "share")' in code
    assert 'ensure_temporary_cache_dir("~/.cache", "/content/colab-terminal-cache")' in code


def test_setup_cell_can_auto_install_opencode_for_opencode_mode():
    code = setup_cell_code(
        port=7681,
        cwd="/content",
        install_timeout=600,
        terminal_command="opencode",
    )

    compile(code, "<colab-terminal-opencode-setup>", "exec")
    assert "TERMINAL_COMMAND = 'opencode'" in code
    assert "install_opencode()" in code
    assert "run(\"opencode --version\", timeout=60)" in code
```

- [x] **Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest tests/opencode_setup_cell_test.py -q
```

Expected: the new tests fail because the current defaults still use `/content/drive/MyDrive/opencode`, `opencode.ipynb`, and `TERMINAL_COMMAND = 'opencode'`.

- [x] **Step 3: Update setup defaults and generated persistence code**

In `scripts/colab_opencode_web_terminal.py`, set:

```python
DEFAULT_DRIVE_FOLDER = "/content/drive/MyDrive/colab-terminal"
DEFAULT_NOTEBOOK_NAME = "colab-terminal.ipynb"
DEFAULT_TERMINAL_COMMAND = "shell"
DEFAULT_GHOSTTOWN_TMUX_SESSION = "drive-terminal"
```

Add a generated helper inside `setup_cell_code()`:

```python
def ensure_temporary_cache_dir(runtime_path, cache_path):
    runtime = Path(runtime_path).expanduser()
    cache = Path(cache_path)
    cache.mkdir(parents=True, exist_ok=True)
    runtime.parent.mkdir(parents=True, exist_ok=True)
    if runtime.is_symlink():
        try:
            if runtime.resolve() == cache.resolve():
                return {"runtime": str(runtime), "target": str(cache), "linked": True, "temporary": True, "alreadyLinked": True}
        except FileNotFoundError:
            pass
        runtime.unlink()
    elif runtime.exists():
        merge_existing_directory(runtime, cache)
    runtime.symlink_to(cache, target_is_directory=True)
    return {"runtime": str(runtime), "target": str(cache), "linked": True, "temporary": True}
```

Replace the Drive persistence links with:

```python
PERSISTENCE_LINKS = [
    ensure_persistent_dir("~/.config", drive_root / "home" / ".config"),
    ensure_persistent_dir("~/.local/share", drive_root / "home" / ".local" / "share"),
    ensure_temporary_cache_dir("~/.cache", "/content/colab-terminal-cache"),
]
```

Only install OpenCode in generated code when OpenCode mode is selected:

```python
if TERMINAL_COMMAND == "opencode":
    install_opencode()
    run("opencode --version", timeout=60)
```

Emit the new marker while keeping the old marker for compatibility:

```python
payload = json.dumps(result, sort_keys=True)
emit("COLAB_TERMINAL_RESULT " + payload)
emit("COLAB_OPENCODE_RESULT " + payload)
```

- [x] **Step 4: Update local bridge labels and parser compatibility**

In `scripts/colab_opencode_localhost.py`, update user-facing prints from OpenCode-only names to terminal names:

```python
print(f"Terminal backend: {setup.get('terminalBackend')}", flush=True)
print(f"Terminal workdir: {setup.get('workdir')}", flush=True)
print(f"Terminal recovery files: {json.dumps(setup.get('recoveryFiles') or [])}", flush=True)
```

Update `parse_setup_result()` to prefer `COLAB_TERMINAL_RESULT` and fall back to `COLAB_OPENCODE_RESULT`:

```python
for marker in ("COLAB_TERMINAL_RESULT ", "COLAB_OPENCODE_RESULT "):
    marker_index = output.find(marker)
    if marker_index >= 0:
        decoder = json.JSONDecoder()
        payload = output[marker_index + len(marker):].lstrip()
        result, _end = decoder.raw_decode(payload)
        if not isinstance(result, dict):
            raise RuntimeError(f"Colab terminal setup emitted non-object result: {result!r}")
        return result
raise RuntimeError("Colab terminal setup did not emit COLAB_TERMINAL_RESULT.")
```

- [x] **Step 5: Run focused tests**

Run:

```bash
uv run pytest tests/opencode_setup_cell_test.py -q
```

Expected: all setup-cell tests pass.

- [x] **Step 6: Commit Task 1**

Run:

```bash
git add -A
git status --short
git commit -m "feat: make Colab terminal shell-first"
git push fork master
```

Expected: status shows only intended Task 1 files staged before commit; push succeeds.

## Task 2: Wizard Profile Discovery And Command Builder

**Files:**
- Create: `src/colab_mcp/drive_terminal_wizard.py`
- Create: `tests/drive_terminal_wizard_test.py`

- [x] **Step 1: Write failing profile discovery tests**

Create `tests/drive_terminal_wizard_test.py`:

```python
import json
from pathlib import Path

import pytest

from colab_mcp.drive_terminal_wizard import (
    ChromeProfile,
    WorkspaceChoice,
    build_bridge_command,
    choose_workspace,
    load_chrome_profiles,
)


def write_local_state(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "Local State").write_text(
        json.dumps(
            {
                "profile": {
                    "info_cache": {
                        "Default": {
                            "name": "Your Chrome",
                            "gaia_name": "nothumanatall",
                            "user_name": "canbehumanagain@gmail.com",
                            "is_consented_primary_account": False,
                        },
                        "Profile 32": {
                            "name": "Awanish",
                            "gaia_name": "Awanish Maurya",
                            "user_name": "cloudboosterawanish@gmail.com",
                            "is_consented_primary_account": True,
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_load_chrome_profiles_reads_names_and_primary_status(tmp_path):
    write_local_state(tmp_path)

    profiles = load_chrome_profiles(tmp_path)

    assert profiles == [
        ChromeProfile("Profile 32", "Awanish", "Awanish Maurya", "cloudboosterawanish@gmail.com", True),
        ChromeProfile("Default", "Your Chrome", "nothumanatall", "canbehumanagain@gmail.com", False),
    ]


def test_choose_workspace_drive_default():
    workspace = choose_workspace(mode="drive", project_name="demo", allow_temp=False)

    assert workspace == WorkspaceChoice(
        mode="drive",
        project_name="demo",
        drive_folder="/content/drive/MyDrive/colab-terminal",
        cwd="/content",
        require_drive=True,
        drive_persistence=True,
    )


def test_choose_workspace_temp_requires_allow_temp():
    with pytest.raises(ValueError, match="Temporary /content mode requires explicit confirmation"):
        choose_workspace(mode="temp", project_name="demo", allow_temp=False)


def test_build_bridge_command_uses_shell_and_profile_copy(tmp_path):
    profile = ChromeProfile("Profile 32", "Awanish", "Awanish Maurya", "cloudboosterawanish@gmail.com", True)
    workspace = choose_workspace(mode="drive", project_name="demo", allow_temp=False)

    command = build_bridge_command(
        repo=tmp_path,
        profile=profile,
        workspace=workspace,
        profile_copy_dir=Path("/tmp/colab-mcp-profile32-copy"),
        cdp_port=9463,
        local_port=8768,
        colab_port=7686,
    )

    assert command[:3] == ["uv", "run", "python"]
    assert "scripts/colab_opencode_localhost.py" in command
    assert "--terminal-command" in command
    assert command[command.index("--terminal-command") + 1] == "shell"
    assert command[command.index("--browser-profile") + 1] == "Profile 32"
    assert command[command.index("--drive-folder") + 1] == "/content/drive/MyDrive/colab-terminal"
```

- [x] **Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest tests/drive_terminal_wizard_test.py -q
```

Expected: import fails because `colab_mcp.drive_terminal_wizard` does not exist.

- [x] **Step 3: Implement profile and workspace helpers**

Create `src/colab_mcp/drive_terminal_wizard.py` with:

```python
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys


DEFAULT_DRIVE_ROOT = "/content/drive/MyDrive/colab-terminal"
DEFAULT_TEMP_ROOT = "/content/colab-terminal"
DEFAULT_PROFILE_COPY_DIR = Path("/tmp/colab-mcp-drive-terminal-profile-copy")


@dataclass(frozen=True)
class ChromeProfile:
    directory: str
    display_name: str
    gaia_name: str
    user_name: str
    is_primary: bool


@dataclass(frozen=True)
class WorkspaceChoice:
    mode: str
    project_name: str
    drive_folder: str
    cwd: str
    require_drive: bool
    drive_persistence: bool


def default_chrome_user_data_dir() -> Path:
    return Path(os.environ.get("COLAB_MCP_BROWSER_USER_DATA_DIR", Path.home() / ".config" / "google-chrome")).expanduser()


def load_chrome_profiles(user_data_dir: Path) -> list[ChromeProfile]:
    local_state = user_data_dir / "Local State"
    data = json.loads(local_state.read_text(encoding="utf-8"))
    info_cache = data.get("profile", {}).get("info_cache", {})
    profiles = [
        ChromeProfile(
            directory=str(directory),
            display_name=str(info.get("name") or directory),
            gaia_name=str(info.get("gaia_name") or info.get("gaia_given_name") or ""),
            user_name=str(info.get("user_name") or ""),
            is_primary=bool(info.get("is_consented_primary_account")),
        )
        for directory, info in info_cache.items()
    ]
    return sorted(profiles, key=lambda item: (not item.is_primary, item.directory.lower()))


def choose_workspace(
    *,
    mode: str,
    project_name: str,
    allow_temp: bool,
    drive_root: str = DEFAULT_DRIVE_ROOT,
    temp_root: str = DEFAULT_TEMP_ROOT,
) -> WorkspaceChoice:
    clean_name = project_name.strip() or "project"
    if mode == "drive":
        return WorkspaceChoice("drive", clean_name, drive_root, "/content", True, True)
    if mode == "temp":
        if not allow_temp:
            raise ValueError("Temporary /content mode requires explicit confirmation")
        return WorkspaceChoice("temp", clean_name, "", f"{temp_root}/projects/{clean_name}", False, False)
    raise ValueError(f"Unknown workspace mode: {mode}")
```

- [x] **Step 4: Implement command builder**

Append to `src/colab_mcp/drive_terminal_wizard.py`:

```python
def build_bridge_command(
    *,
    repo: Path,
    profile: ChromeProfile,
    workspace: WorkspaceChoice,
    profile_copy_dir: Path,
    cdp_port: int,
    local_port: int,
    colab_port: int,
    refresh_profile_copy: bool = False,
    browser_headless: bool = False,
) -> list[str]:
    command = [
        "uv",
        "run",
        "python",
        "scripts/colab_opencode_localhost.py",
        "--repo",
        str(repo),
        "--terminal-backend",
        "ghosttown",
        "--terminal-command",
        "shell",
        "--ghosttown-session-mode",
        "tmux",
        "--ghosttown-tmux-session",
        "drive-terminal",
        "--browser-copy-profile",
        "--browser-profile",
        profile.directory,
        "--browser-profile-copy-dir",
        str(profile_copy_dir),
        "--cdp-port",
        str(cdp_port),
        "--local-port",
        str(local_port),
        "--colab-port",
        str(colab_port),
        "--cwd",
        workspace.cwd,
    ]
    command.append("--browser-headless" if browser_headless else "--no-browser-headless")
    command.append("--no-browser-reuse-profile-copy" if refresh_profile_copy else "--browser-reuse-profile-copy")
    if workspace.drive_persistence:
        command.extend(["--drive-persistence", "--require-drive", "--drive-folder", workspace.drive_folder])
    else:
        command.extend(["--no-drive-persistence", "--no-require-drive"])
    return command
```

- [x] **Step 5: Run focused tests**

Run:

```bash
uv run pytest tests/drive_terminal_wizard_test.py -q
```

Expected: all wizard helper tests pass.

- [ ] **Step 6: Commit Task 2**

Run:

```bash
git add -A
git status --short
git commit -m "feat: add Colab terminal wizard helpers"
git push fork master
```

Expected: status shows the new wizard module and tests staged before commit; push succeeds.

## Task 3: Interactive Wizard CLI And Entry Point

**Files:**
- Modify: `src/colab_mcp/drive_terminal_wizard.py`
- Create: `scripts/colab_drive_terminal.py`
- Modify: `pyproject.toml`
- Modify: `tests/drive_terminal_wizard_test.py`

- [ ] **Step 1: Write failing CLI tests**

Append to `tests/drive_terminal_wizard_test.py`:

```python
def test_parse_args_defaults_to_interactive_shell():
    from colab_mcp.drive_terminal_wizard import parse_args

    args = parse_args([])

    assert args.workspace == "interactive"
    assert args.project == "project"
    assert args.local_port == 8768
    assert args.colab_port == 7686


def test_script_entrypoint_imports_packaged_main():
    wrapper = Path("scripts/colab_drive_terminal.py").read_text(encoding="utf-8")

    assert "from colab_mcp.drive_terminal_wizard import main" in wrapper
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
uv run pytest tests/drive_terminal_wizard_test.py -q
```

Expected: `parse_args` and wrapper file checks fail.

- [ ] **Step 3: Add prompt helpers and CLI execution**

Append to `src/colab_mcp/drive_terminal_wizard.py`:

```python
def prompt_profile(profiles: list[ChromeProfile]) -> ChromeProfile:
    if not profiles:
        raise RuntimeError("No Chrome profiles were found in Local State.")
    print("Chrome profiles:")
    for index, profile in enumerate(profiles, start=1):
        primary = " primary" if profile.is_primary else ""
        account = profile.user_name or profile.gaia_name or "no account metadata"
        print(f"{index}. {profile.directory} - {profile.display_name} - {account}{primary}")
    while True:
        answer = input("Select Chrome profile: ").strip()
        for index, profile in enumerate(profiles, start=1):
            if answer == str(index) or answer == profile.directory or answer == profile.display_name:
                return profile
        print("Unknown profile selection.")


def prompt_workspace(project_name: str) -> WorkspaceChoice:
    print("Workspace modes:")
    print("1. Drive workspace recommended")
    print("2. Temporary /content workspace")
    answer = input("Select workspace mode [1]: ").strip() or "1"
    if answer == "1":
        return choose_workspace(mode="drive", project_name=project_name, allow_temp=False)
    if answer == "2":
        print("Temporary /content mode is not durable. Runtime reset can delete files and sessions.")
        confirm = input("Type allow-temp to continue: ").strip()
        return choose_workspace(mode="temp", project_name=project_name, allow_temp=confirm == "allow-temp")
    raise ValueError("Unknown workspace mode selection")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open a Drive-backed Colab terminal through MCP.")
    parser.add_argument("--chrome-user-data-dir", type=Path, default=default_chrome_user_data_dir())
    parser.add_argument("--profile")
    parser.add_argument("--workspace", choices=("interactive", "drive", "temp"), default="interactive")
    parser.add_argument("--allow-temp", action="store_true")
    parser.add_argument("--project", default="project")
    parser.add_argument("--profile-copy-dir", type=Path, default=DEFAULT_PROFILE_COPY_DIR)
    parser.add_argument("--refresh-profile-copy", action="store_true")
    parser.add_argument("--cdp-port", type=int, default=9463)
    parser.add_argument("--local-port", type=int, default=8768)
    parser.add_argument("--colab-port", type=int, default=7686)
    parser.add_argument("--browser-headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    return parser.parse_args(argv)


def resolve_profile(profiles: list[ChromeProfile], selected: str | None) -> ChromeProfile:
    if selected is None:
        return prompt_profile(profiles)
    for profile in profiles:
        if selected in {profile.directory, profile.display_name, profile.user_name, profile.gaia_name}:
            return profile
    raise RuntimeError(f"Chrome profile not found: {selected}")


def run_wizard(args: argparse.Namespace) -> int:
    profiles = load_chrome_profiles(args.chrome_user_data_dir)
    profile = resolve_profile(profiles, args.profile)
    if args.workspace == "interactive":
        workspace = prompt_workspace(args.project)
    else:
        workspace = choose_workspace(mode=args.workspace, project_name=args.project, allow_temp=args.allow_temp)
    command = build_bridge_command(
        repo=args.repo,
        profile=profile,
        workspace=workspace,
        profile_copy_dir=args.profile_copy_dir,
        cdp_port=args.cdp_port,
        local_port=args.local_port,
        colab_port=args.colab_port,
        refresh_profile_copy=args.refresh_profile_copy,
        browser_headless=args.browser_headless,
    )
    print("Launching Colab terminal:")
    print(" ".join(command))
    if args.dry_run:
        return 0
    return subprocess.call(command, cwd=args.repo)


def main(argv: list[str] | None = None) -> int:
    return run_wizard(parse_args(argv))
```

- [ ] **Step 4: Add script wrapper and console script**

Create `scripts/colab_drive_terminal.py`:

```python
#!/usr/bin/env python3
"""Interactive launcher for a Drive-backed Colab terminal."""

from colab_mcp.drive_terminal_wizard import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Add to `[project.scripts]` in `pyproject.toml`:

```toml
colab-drive-terminal = "colab_mcp.drive_terminal_wizard:main"
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
uv run pytest tests/drive_terminal_wizard_test.py -q
```

Expected: all wizard tests pass.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add -A
git status --short
git commit -m "feat: add interactive Colab terminal wizard"
git push fork master
```

Expected: status shows CLI wrapper, wizard module, tests, and pyproject staged before commit; push succeeds.

## Task 4: Documentation, Version, And Changelog

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/OPENCODE_COLAB.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `docs/steps.md`

- [ ] **Step 1: Bump package version**

Set `pyproject.toml`:

```toml
version = "0.10.0"
```

Refresh the lockfile:

```bash
uv lock
```

Expected: `uv.lock` package version is `0.10.0`.

- [ ] **Step 2: Update changelog**

Add to the top of `CHANGELOG.md`:

```markdown
## v0.10.0 - 2026-06-07

- Added `colab-drive-terminal`, an interactive wizard for selecting a signed-in Chrome profile and launching a Drive-backed native Colab Ubuntu shell.
- Changed terminal defaults from OpenCode-first to shell-first; OpenCode remains available as an explicit mode or manual install from the shell.
- Added Drive-first workspace persistence under `/content/drive/MyDrive/colab-terminal` with XDG config and app-data persistence.
- Added explicit temporary `/content` fallback guarded by interactive confirmation or `--allow-temp`.
```

- [ ] **Step 3: Update user docs**

Add this quick start to `docs/OPENCODE_COLAB.md`:

```markdown
## Colab Drive Terminal Wizard

Run the interactive wizard:

```shell
uv run colab-drive-terminal
```

The wizard scans Chrome profiles, lets you select the signed-in Google account, connects Colab MCP, mounts Drive, and opens a native Ubuntu shell in:

```text
/content/drive/MyDrive/colab-terminal/projects/<project-name>
```

OpenCode is not started by default. Install it inside the shell when needed:

```shell
curl -fsSL https://opencode.ai/install | bash
opencode
```
```

- [ ] **Step 4: Commit Task 4**

Run:

```bash
git add -A
git status --short
git commit -m "docs: document Colab terminal wizard"
git push fork master
```

Expected: docs, changelog, version, and lockfile changes are pushed.

## Task 5: Full Validation And Release

**Files:**
- Modify: `docs/steps.md`

- [ ] **Step 1: Run all automated checks**

Run:

```bash
bash -n scripts/launch_colab_drive_terminal.sh
python -m py_compile scripts/colab_drive_terminal.py
uv run pytest -q
git diff --check
```

Expected:
- shell script syntax passes
- wrapper compiles
- pytest passes
- no whitespace errors

- [ ] **Step 2: Run dry-run wizard validation**

Run:

```bash
uv run colab-drive-terminal --profile 'Profile 32' --workspace drive --project smoke --dry-run
uv run colab-drive-terminal --profile 'Profile 32' --workspace temp --project smoke --allow-temp --dry-run
```

Expected:
- both commands print the bridge command
- drive command includes `--drive-persistence --require-drive`
- temp command includes `--no-drive-persistence --no-require-drive`

- [ ] **Step 3: Run live smoke if authenticated profile is available**

Run:

```bash
uv run colab-drive-terminal --profile 'Profile 32' --workspace drive --project smoke --refresh-profile-copy --dry-run
```

Then run the printed command with `--exit-after-smoke` appended if a signed-in profile is available and no stale Colab session is blocking the port.

Expected:
- MCP connects
- runtime connects
- terminal setup opens localhost
- Drive mount either succeeds or reports the exact Drive authorization blocker

- [ ] **Step 4: Log validation result**

Append a `docs/steps.md` entry with the exact commands, result, and timestamp.

- [ ] **Step 5: Commit validation log**

Run:

```bash
git add -A
git status --short
git commit -m "docs: record Colab terminal wizard validation"
git push fork master
```

Expected: validation log is pushed.

- [ ] **Step 6: Tag and push `v0.10.0`**

Run:

```bash
git tag v0.10.0
git push fork --tags
```

Expected: `v0.10.0` appears on the fork.

## Self-Review

- Spec coverage: the plan covers Chrome profile selection, Drive-first persistence, explicit temp fallback, native Ubuntu shell default, XDG config/app-data persistence, optional OpenCode, docs, tests, and release.
- Placeholder scan: no incomplete marker text is present.
- Type consistency: `ChromeProfile`, `WorkspaceChoice`, `load_chrome_profiles`, `choose_workspace`, `build_bridge_command`, `parse_args`, and `run_wizard` are defined before they are used.
- Scope: proot distro mode is intentionally deferred per the approved spec.
