import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from colab_opencode_web_terminal import setup_cell_code  # noqa: E402


def test_setup_cell_code_compiles_for_ttyd_backend():
    code = setup_cell_code(port=7681, cwd="/content", install_timeout=600, terminal_backend="ttyd")

    compile(code, "<opencode-ttyd-setup>", "exec")
    assert "install_ttyd()" in code
    assert "start_ttyd()" in code
    assert "colab-terminal.ipynb" in code
    assert "ensure_persistent_dir" in code


def test_setup_cell_defaults_to_shell_and_colab_terminal_drive_root():
    code = setup_cell_code(port=7681, cwd="/content", install_timeout=600)

    compile(code, "<colab-terminal-default-setup>", "exec")
    assert "TERMINAL_COMMAND = 'shell'" in code
    assert "DRIVE_FOLDER = '/content/drive/MyDrive/colab-terminal'" in code
    assert "NOTEBOOK_NAME = 'colab-terminal.ipynb'" in code
    assert "COLAB_TERMINAL_RESULT " in code
    assert '\ninstall_opencode()\nrun("opencode --version", timeout=60)' not in code


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
    assert 'run("opencode --version", timeout=60)' in code


def test_setup_cell_code_compiles_for_ghosttown_backend():
    code = setup_cell_code(port=7681, cwd="/content", install_timeout=600, terminal_backend="ghosttown")

    compile(code, "<opencode-ghosttown-setup>", "exec")
    assert "install_ghosttown()" in code
    assert "start_ghosttown()" in code
    assert "ghosttown -p " in code
    assert "write_ghosttown_shell()" in code
    assert "SHELL=" in code
    assert "colab-terminal-ghosttown-shell.sh" in code


def test_setup_cell_code_compiles_for_ghosttown_tmux_mode():
    code = setup_cell_code(
        port=7681,
        cwd="/content",
        install_timeout=600,
        terminal_backend="ghosttown",
        ghosttown_session_mode="tmux",
        ghosttown_tmux_session="opencode",
    )

    compile(code, "<opencode-ghosttown-tmux-setup>", "exec")
    assert "GHOSTTOWN_SESSION_MODE = 'tmux'" in code
    assert "GHOSTTOWN_TMUX_SESSION = 'opencode'" in code
    assert "tmux new-session -d -s" in code
    assert "exec tmux attach-session -t" in code
    assert "ghosttownTmuxAttachCommand" in code


def test_setup_cell_code_compiles_for_drive_rooted_shell_mode():
    code = setup_cell_code(
        port=7681,
        cwd="/content",
        install_timeout=600,
        terminal_backend="ghosttown",
        terminal_command="shell",
        ghosttown_session_mode="tmux",
        ghosttown_tmux_session="drive-terminal",
    )

    compile(code, "<opencode-ghosttown-shell-tmux-setup>", "exec")
    assert "TERMINAL_COMMAND = 'shell'" in code
    assert "exec /bin/bash -l" in code
    assert "terminalCommand" in code
    assert "terminalLaunchCommand" in code
    assert "GHOSTTOWN_TMUX_SESSION = 'drive-terminal'" in code


def test_setup_cell_code_can_disable_drive_persistence():
    code = setup_cell_code(
        port=7681,
        cwd="/content/project",
        install_timeout=600,
        drive_persistence=False,
    )

    compile(code, "<opencode-no-drive-setup>", "exec")
    assert "DRIVE_PERSISTENCE = False" in code
    assert "WORKDIR_REQUEST = '/content/project'" in code
