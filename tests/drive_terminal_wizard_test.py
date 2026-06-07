import json
from pathlib import Path

import pytest

from colab_mcp.drive_terminal_wizard import (
    ChromeProfile,
    WorkspaceChoice,
    build_bridge_command,
    choose_workspace,
    default_profile_copy_dir,
    load_chrome_profiles,
    prompt_profile,
)


def write_local_state(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
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
        cwd="/content/drive/MyDrive/colab-terminal/projects/demo",
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
    assert command[command.index("--cwd") + 1] == "/content/drive/MyDrive/colab-terminal/projects/demo"


def test_build_bridge_command_derives_default_copy_dir_per_profile(tmp_path):
    profile = ChromeProfile("Profile 32", "Awanish", "Awanish Maurya", "cloudboosterawanish@gmail.com", True)
    workspace = choose_workspace(mode="drive", project_name="demo", allow_temp=False)

    command = build_bridge_command(
        repo=tmp_path,
        profile=profile,
        workspace=workspace,
        profile_copy_dir=None,
        cdp_port=9463,
        local_port=8768,
        colab_port=7686,
    )

    assert command[command.index("--browser-profile-copy-dir") + 1] == str(default_profile_copy_dir(profile))
    assert command[command.index("--browser-profile-copy-dir") + 1].endswith("-profile-32")


def test_prompt_profile_defaults_back_to_primary_when_nonprimary_selected(monkeypatch):
    primary = ChromeProfile("Profile 32", "Awanish", "Awanish Maurya", "cloudboosterawanish@gmail.com", True)
    nonprimary = ChromeProfile("Default", "Your Chrome", "nothumanatall", "canbehumanagain@gmail.com", False)
    answers = iter(["2", ""])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    selected = prompt_profile([primary, nonprimary])

    assert selected == primary


def test_prompt_profile_can_continue_with_nonprimary_after_explicit_confirmation(monkeypatch):
    primary = ChromeProfile("Profile 32", "Awanish", "Awanish Maurya", "cloudboosterawanish@gmail.com", True)
    nonprimary = ChromeProfile("Default", "Your Chrome", "nothumanatall", "canbehumanagain@gmail.com", False)
    answers = iter(["2", "use-non-primary"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    selected = prompt_profile([primary, nonprimary])

    assert selected == nonprimary


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
