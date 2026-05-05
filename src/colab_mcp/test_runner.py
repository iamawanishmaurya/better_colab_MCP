import argparse
import subprocess
import sys


def run(command: list[str]) -> int:
    completed = subprocess.run(command)
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local colab-mcp test checks.")
    parser.add_argument("--browser", action="store_true", help="Also run browser smoke test through colabctl.")
    parser.add_argument("--port", type=int, default=9222)
    args = parser.parse_args()

    rc = run([sys.executable, "-m", "pytest", "-q"])
    if rc != 0:
        raise SystemExit(rc)

    if args.browser:
        rc = run([sys.executable, "-m", "colab_mcp.colabctl", "--port", str(args.port), "smoke-browser"])
        if rc != 0:
            raise SystemExit(rc)
