from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess


DEFAULT_DRIVE_ROOT = "/content/drive/MyDrive/colab-terminal"
DEFAULT_TEMP_ROOT = "/content/colab-terminal"
DEFAULT_PROFILE_COPY_DIR = Path("/tmp/colab-mcp-drive-terminal-profile-copy")
DEFAULT_REPO = Path(__file__).resolve().parents[2]


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


def _path_slug(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "profile"


def default_profile_copy_dir(profile: ChromeProfile) -> Path:
    return DEFAULT_PROFILE_COPY_DIR.with_name(
        DEFAULT_PROFILE_COPY_DIR.name + "-" + _path_slug(profile.directory)
    )


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
    profile_copy_dir: Path | None,
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
        str(profile_copy_dir or default_profile_copy_dir(profile)),
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
            if answer in {str(index), profile.directory, profile.display_name}:
                if not profile.is_primary:
                    primary = next((item for item in profiles if item.is_primary), None)
                    if primary is not None:
                        print(
                            "Warning: this profile is not Chrome's primary signed-in profile. "
                            "Copied Colab auth may show Sign in."
                        )
                        confirm = input(
                            "Press Enter to use "
                            + primary.directory
                            + ", or type use-non-primary to continue: "
                        ).strip()
                        if confirm != "use-non-primary":
                            return primary
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
    parser.add_argument("--profile-copy-dir", type=Path)
    parser.add_argument("--refresh-profile-copy", action="store_true")
    parser.add_argument("--cdp-port", type=int, default=9463)
    parser.add_argument("--local-port", type=int, default=8768)
    parser.add_argument("--colab-port", type=int, default=7686)
    parser.add_argument("--browser-headless", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    args = parser.parse_args(argv)
    if args.local_port <= 0 or args.local_port > 65535:
        parser.error("--local-port must be between 1 and 65535")
    if args.colab_port <= 0 or args.colab_port > 65535:
        parser.error("--colab-port must be between 1 and 65535")
    if args.cdp_port <= 0 or args.cdp_port > 65535:
        parser.error("--cdp-port must be between 1 and 65535")
    return args


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
        workspace = choose_workspace(
            mode=args.workspace,
            project_name=args.project,
            allow_temp=args.allow_temp,
        )
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
