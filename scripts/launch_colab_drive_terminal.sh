#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_default=$(cd -- "$script_dir/.." && pwd)

repo=${COLAB_DRIVE_TERMINAL_REPO:-$repo_default}
terminal_command=${COLAB_OPENCODE_TERMINAL_COMMAND:-shell}
session=${COLAB_DRIVE_TERMINAL_SESSION:-colab-drive-terminal-cdp}
ghosttown_tmux_session=${COLAB_DRIVE_TERMINAL_GHOSTTOWN_TMUX_SESSION:-drive-terminal}
browser_profile=${COLAB_MCP_BROWSER_PROFILE:-Default}
profile_copy_dir=${COLAB_MCP_BROWSER_PROFILE_COPY_DIR:-/tmp/colab-mcp-opencode-realcopy-profile}
cdp_port=${COLAB_MCP_EDGE_CDP_PORT:-9463}
local_port=${COLAB_DRIVE_TERMINAL_LOCAL_PORT:-8768}
colab_port=${COLAB_OPENCODE_PORT:-7686}
setup_timeout=${COLAB_OPENCODE_SETUP_TIMEOUT:-1200}
install_timeout=${COLAB_OPENCODE_INSTALL_TIMEOUT:-900}
drive_mount_timeout=${COLAB_OPENCODE_DRIVE_MOUNT_TIMEOUT:-180}
log_dir=${COLAB_DRIVE_TERMINAL_LOG_DIR:-${TMPDIR:-/tmp}}
browser_headless=0
require_drive=1
reuse_profile_copy=1
open_browser=1
tail_log=1
replace_session=1
exit_after_smoke=0
extra_args=()

usage() {
  cat <<'EOF'
Usage:
  scripts/launch_colab_drive_terminal.sh [shell|opencode] [options] [-- extra bridge args...]

Default mode is "shell": a normal Bash terminal rooted in the Drive-backed
/content/drive/MyDrive/colab-terminal/projects/project folder when Drive mounts.

Options:
  --local-port PORT              Local localhost port. Default: 8768
  --colab-port PORT              Colab terminal backend port. Default: 7686
  --cdp-port PORT                Chrome CDP port. Default: 9463
  --session NAME                 Local tmux session name. Default: colab-drive-terminal-cdp
  --ghosttown-tmux-session NAME  Colab tmux session name. Default: drive-terminal
  --profile NAME                 Chrome profile name. Default: Default
  --profile-copy-dir DIR         Dedicated copied Chrome profile directory.
  --browser-headless             Run the controlled browser headless.
  --no-browser-headless          Run the controlled browser visibly. Default.
  --reuse-profile-copy           Reuse an existing copied Chrome profile. Default.
  --refresh-profile-copy         Rebuild the copied profile from the source profile.
  --require-drive                Fail setup if Drive cannot mount. Default.
  --no-require-drive             Allow temporary runtime fallback if Drive mount fails.
  --open                         Open http://127.0.0.1:PORT/new when ready. Default.
  --no-open                      Do not open the localhost URL.
  --tail                         Tail the fresh bridge log. Default.
  --no-tail                      Start tmux and print log paths without tailing.
  --keep-existing                Refuse to replace an existing local tmux session.
  --exit-after-smoke             Stop after localhost smoke validation.
  --setup-timeout SECONDS        Colab setup cell timeout. Default: 1200
  --install-timeout SECONDS      Opencode/backend install timeout. Default: 900
  --drive-mount-timeout SECONDS  Drive mount timeout. Default: 180
  --repo PATH                    Repository path. Default: script parent.
  -h, --help                     Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    shell|opencode)
      terminal_command=$1
      shift
      ;;
    --local-port)
      local_port=$2
      shift 2
      ;;
    --colab-port)
      colab_port=$2
      shift 2
      ;;
    --cdp-port)
      cdp_port=$2
      shift 2
      ;;
    --session)
      session=$2
      shift 2
      ;;
    --ghosttown-tmux-session)
      ghosttown_tmux_session=$2
      shift 2
      ;;
    --profile)
      browser_profile=$2
      shift 2
      ;;
    --profile-copy-dir)
      profile_copy_dir=$2
      shift 2
      ;;
    --browser-headless)
      browser_headless=1
      shift
      ;;
    --no-browser-headless)
      browser_headless=0
      shift
      ;;
    --reuse-profile-copy)
      reuse_profile_copy=1
      shift
      ;;
    --refresh-profile-copy)
      reuse_profile_copy=0
      shift
      ;;
    --require-drive)
      require_drive=1
      shift
      ;;
    --no-require-drive)
      require_drive=0
      shift
      ;;
    --open)
      open_browser=1
      shift
      ;;
    --no-open)
      open_browser=0
      shift
      ;;
    --tail)
      tail_log=1
      shift
      ;;
    --no-tail)
      tail_log=0
      shift
      ;;
    --keep-existing)
      replace_session=0
      shift
      ;;
    --exit-after-smoke)
      exit_after_smoke=1
      shift
      ;;
    --setup-timeout)
      setup_timeout=$2
      shift 2
      ;;
    --install-timeout)
      install_timeout=$2
      shift 2
      ;;
    --drive-mount-timeout)
      drive_mount_timeout=$2
      shift 2
      ;;
    --repo)
      repo=$2
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      extra_args+=("$@")
      break
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$terminal_command" != "shell" && "$terminal_command" != "opencode" ]]; then
  echo "Terminal command must be 'shell' or 'opencode'." >&2
  exit 2
fi

if [[ ! -d "$repo" ]]; then
  echo "Repository path does not exist: $repo" >&2
  exit 2
fi

mkdir -p "$log_dir"
safe_session=${session//[^A-Za-z0-9_.-]/_}
timestamp=$(date +%Y%m%d-%H%M%S)
bridge_log="$log_dir/colab-mcp-${safe_session}-${terminal_command}-${timestamp}.log"
mcp_log="$log_dir/colab-mcp-${safe_session}-${terminal_command}-${timestamp}-mcp.log"
runner="$log_dir/colab-mcp-${safe_session}-${terminal_command}-${timestamp}.runner.sh"
local_url="http://127.0.0.1:${local_port}"

bridge_args=(
  scripts/colab_opencode_localhost.py
  --terminal-backend ghosttown
  --terminal-command "$terminal_command"
  --ghosttown-session-mode tmux
  --ghosttown-tmux-session "$ghosttown_tmux_session"
  --browser-copy-profile
  --browser-profile-copy-dir "$profile_copy_dir"
  --browser-profile "$browser_profile"
  --cdp-port "$cdp_port"
  --local-port "$local_port"
  --colab-port "$colab_port"
  --setup-timeout "$setup_timeout"
  --install-timeout "$install_timeout"
  --drive-mount-timeout "$drive_mount_timeout"
  --log-file "$mcp_log"
)

if [[ "$browser_headless" -eq 1 ]]; then
  bridge_args+=(--browser-headless)
else
  bridge_args+=(--no-browser-headless)
fi

if [[ "$reuse_profile_copy" -eq 1 ]]; then
  bridge_args+=(--browser-reuse-profile-copy)
else
  bridge_args+=(--no-browser-reuse-profile-copy)
fi

if [[ "$require_drive" -eq 1 ]]; then
  bridge_args+=(--require-drive)
else
  bridge_args+=(--no-require-drive)
fi

if [[ "$exit_after_smoke" -eq 1 ]]; then
  bridge_args+=(--exit-after-smoke)
fi

bridge_args+=("${extra_args[@]}")

{
  printf 'Launch timestamp: %s\n' "$(date --iso-8601=seconds)"
  printf 'Repository: %s\n' "$repo"
  printf 'Mode: %s\n' "$terminal_command"
  printf 'Local URL: %s/new\n' "$local_url"
  printf 'Outer tmux session: %s\n' "$session"
  printf 'Colab tmux session: %s\n' "$ghosttown_tmux_session"
  printf 'CDP port: %s\n' "$cdp_port"
  printf 'Colab port: %s\n' "$colab_port"
  printf 'Profile copy dir: %s\n' "$profile_copy_dir"
  printf 'Reuse profile copy: %s\n' "$reuse_profile_copy"
  printf '\n'
} > "$bridge_log"

{
  printf '#!/usr/bin/env bash\n'
  printf 'set -euo pipefail\n'
  printf 'cd %q\n' "$repo"
  printf 'exec uv run python'
  printf ' %q' "${bridge_args[@]}"
  printf ' >> %q 2>&1\n' "$bridge_log"
} > "$runner"
chmod +x "$runner"

if tmux has-session -t "$session" 2>/dev/null; then
  if [[ "$replace_session" -eq 0 ]]; then
    echo "tmux session already exists: $session" >&2
    echo "Attach with: tmux attach -t $session" >&2
    exit 1
  fi
  tmux kill-session -t "$session"
fi

stop_controlled_chrome() {
  local pattern=$1
  local pids=()
  local line pid
  while IFS= read -r line; do
    [[ "$line" == *chrome* || "$line" == *chromium* ]] || continue
    pid=${line%% *}
    [[ -n "$pid" && "$pid" != "$$" ]] || continue
    pids+=("$pid")
  done < <(pgrep -af -- "$pattern" || true)
  if [[ "${#pids[@]}" -gt 0 ]]; then
    kill "${pids[@]}" 2>/dev/null || true
    sleep 1
  fi
}

if [[ "$reuse_profile_copy" -eq 0 ]]; then
  stop_controlled_chrome "remote-debugging-port=${cdp_port}"
  stop_controlled_chrome "user-data-dir=${profile_copy_dir}"
fi

tmux new-session -d -s "$session" "$runner"

echo "Started Colab Drive terminal launcher."
echo "Mode: $terminal_command"
echo "Local URL when ready: $local_url/new"
echo "Attach tmux: tmux attach -t $session"
echo "Bridge log: $bridge_log"
echo "MCP log: $mcp_log"

wait_for_localhost() {
  local deadline=$((SECONDS + setup_timeout + install_timeout + drive_mount_timeout + 300))
  while (( SECONDS < deadline )); do
    if curl -fsS --max-time 2 "$local_url/new" >/dev/null 2>&1; then
      return 0
    fi
    if ! tmux has-session -t "$session" 2>/dev/null; then
      echo "tmux session exited before localhost was ready." >&2
      tail -n 80 "$bridge_log" >&2 || true
      return 1
    fi
    sleep 2
  done
  echo "Timed out waiting for $local_url/new." >&2
  tail -n 80 "$bridge_log" >&2 || true
  return 1
}

open_when_ready() {
  if wait_for_localhost; then
    echo "Opening $local_url/new"
    xdg-open "$local_url/new" >/dev/null 2>&1 || true
  fi
}

if [[ "$open_browser" -eq 1 ]]; then
  if command -v xdg-open >/dev/null 2>&1; then
    if [[ "$tail_log" -eq 1 ]]; then
      open_when_ready &
    else
      open_when_ready
    fi
  else
    echo "xdg-open is not available; open this URL when ready: $local_url/new"
  fi
fi

if [[ "$tail_log" -eq 1 ]]; then
  tail -n +1 -f "$bridge_log"
else
  echo "Tailing disabled. Watch with: tail -f $bridge_log"
fi
