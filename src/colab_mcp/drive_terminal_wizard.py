from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path


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
    configured = os.environ.get("COLAB_MCP_BROWSER_USER_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config" / "google-chrome"


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


def _clean_project_name(project_name: str) -> str:
    clean_name = project_name.strip()
    return clean_name or "project"


def choose_workspace(
    *,
    mode: str,
    project_name: str,
    allow_temp: bool,
    drive_root: str = DEFAULT_DRIVE_ROOT,
    temp_root: str = DEFAULT_TEMP_ROOT,
) -> WorkspaceChoice:
    clean_name = _clean_project_name(project_name)
    if mode == "drive":
        return WorkspaceChoice(
            mode="drive",
            project_name=clean_name,
            drive_folder=drive_root,
            cwd=f"{drive_root}/projects/{clean_name}",
            require_drive=True,
            drive_persistence=True,
        )
    if mode == "temp":
        if not allow_temp:
            raise ValueError("Temporary /content mode requires explicit confirmation")
        return WorkspaceChoice(
            mode="temp",
            project_name=clean_name,
            drive_folder="",
            cwd=f"{temp_root}/projects/{clean_name}",
            require_drive=False,
            drive_persistence=False,
        )
    raise ValueError(f"Unknown workspace mode: {mode}")


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
    command.append(
        "--no-browser-reuse-profile-copy"
        if refresh_profile_copy
        else "--browser-reuse-profile-copy"
    )
    if workspace.drive_persistence:
        command.extend(["--drive-persistence", "--require-drive", "--drive-folder", workspace.drive_folder])
    else:
        command.extend(["--no-drive-persistence", "--no-require-drive"])
    return command
