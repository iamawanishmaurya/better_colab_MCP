# Colab Drive Terminal Wizard Design

## Goal

Build a command-line wizard that lets a user select an already authenticated Chrome profile, connect Colab MCP automatically, open a native Colab Ubuntu shell, and use Google Drive as the durable workspace and application state store.

The local laptop is only the controller: it provides browser authentication, MCP automation, and a localhost terminal proxy. Colab provides disposable compute. Google Drive provides persistent storage.

## Approved Defaults

- The default terminal is a native Colab Ubuntu shell.
- The default workspace is Drive-backed.
- Temporary `/content` mode is allowed, but only after explicit interactive selection or an explicit automation flag.
- OpenCode is not auto-started by default. The user can install or run it from the shell.
- Alternate distro layers such as Arch, Alpine, or Debian through `proot` are advanced optional modes, not part of the default build.

## Approaches Considered

### Approach 1: Drive-first native Colab shell wizard

The wizard opens a native Ubuntu shell in a Drive-backed workspace and persists standard XDG application state paths into Drive.

Benefits:
- Smallest implementation surface.
- Matches Colab's actual runtime model.
- Keeps project files and application sessions recoverable after runtime reset.
- Avoids forcing OpenCode or any one tool onto the user.

Trade-offs:
- Colab runtime processes still die when the VM is deleted.
- Drive can be slower than local `/content` for many small file operations.

Decision: chosen.

### Approach 2: OpenCode-first launcher

The launcher installs OpenCode and opens it immediately.

Benefits:
- Good for a narrow OpenCode workflow.
- Existing scripts already support this mode.

Trade-offs:
- Too narrow for the new goal.
- Hides the normal shell from the user.
- Makes recovery and state storage feel app-specific instead of terminal-first.

Decision: keep as an optional command or shell command, not the default.

### Approach 3: Proot distro-first terminal

The launcher installs a rootless Arch, Alpine, Debian, or Ubuntu userland using `proot` or similar tooling.

Benefits:
- Gives users a familiar package ecosystem if they want a different distro userland.
- Can be useful for experiments.

Trade-offs:
- Does not replace the Colab kernel or VM.
- No real boot process or normal systemd.
- Slower and more fragile than native Ubuntu.
- Persisting a whole rootfs directly in Drive is risky for performance and quota.

Decision: defer to an advanced optional mode after the native shell wizard is stable.

## Wizard Flow

1. Scan Chrome user-data directories.
2. Read Chrome profile metadata from `Local State`.
3. Present detected profiles with profile directory, display name, Google account name/email when available, and primary account status.
4. Let the user select a profile by number or name.
5. Create or reuse a dedicated copied browser profile for controlled Colab automation.
6. Launch Chrome with CDP and the selected copied profile.
7. Open a Colab scratch notebook or the configured recovery notebook.
8. Auto-fill and connect the local Colab MCP token through CDP.
9. Connect the Colab runtime and check whether the user is signed in.
10. Ask for workspace mode:
    - Drive workspace, recommended.
    - Temporary `/content` workspace, with a warning that runtime reset can delete files.
11. Ask for project name when using Drive mode.
12. Mount Google Drive when Drive mode is selected.
13. Prepare the terminal environment.
14. Start a Ghost Town or ttyd terminal backend.
15. Print and optionally open the local terminal URL.

## Drive Layout

The default persistent root is:

```text
/content/drive/MyDrive/colab-terminal/
```

Inside it:

```text
projects/
  <project-name>/
home/
  .config/
  .local/share/
  .cache/
    <tool-name>/   # optional, tool-specific cache persistence only
sessions/
  terminal-state.json
recovery/
  colab-terminal.ipynb
  reconnect.sh
```

The default shell working directory is:

```text
/content/drive/MyDrive/colab-terminal/projects/<project-name>
```

## Runtime Home Persistence

The setup cell should create a predictable home-state mapping:

```text
~/.config      -> /content/drive/MyDrive/colab-terminal/home/.config
~/.local/share -> /content/drive/MyDrive/colab-terminal/home/.local/share
```

By default, `~/.cache` should remain temporary:

```text
~/.cache -> /content/colab-terminal-cache
```

Tool-specific caches can be persisted only when explicitly selected later. This avoids Drive quota and performance problems caused by heavy cache writes.

## Temporary `/content` Mode

Temporary mode starts the shell under:

```text
/content/colab-terminal/projects/<project-name>
```

The wizard must show a direct warning before using it:

```text
Temporary /content mode is not durable. If Colab resets the runtime, project files, sessions, installed packages, and shell history in /content can be lost.
```

The user must confirm interactively. Automation may use an explicit flag such as `--allow-temp`.

## Terminal Startup

The terminal opens a normal shell by default. It should not start OpenCode automatically.

The startup banner should print:

```text
Workspace: <path>
Persistent config: <path or disabled>
Persistent app data: <path or disabled>
Temporary cache: <path>
Recovery notebook: <path or disabled>
```

The shell should include common paths on `PATH`, including user-local binary locations where tools such as OpenCode may install.

## Reconnect Model

The system cannot keep a Colab process alive after Colab deletes the runtime. It can make recovery easy.

On reconnect, the tool should:

1. Reuse the selected Chrome profile copy when possible.
2. Re-open the Colab notebook.
3. Reconnect MCP and runtime.
4. Remount Drive.
5. Recreate XDG persistence links.
6. Restart the web terminal backend.
7. Return the same local URL pattern when ports are available.

The tool should persist enough metadata to explain what happened and how to recover:

```text
sessions/terminal-state.json
```

This file should include selected profile, workspace mode, project path, terminal backend, local port, Colab port, runtime status, and last setup result.

## Error Handling

- If the selected Chrome profile is not signed into Colab, show diagnostics and let the user choose another profile.
- If the copied profile is stale or anonymous, offer to refresh the copy.
- If Drive mount fails in Drive mode, stop and tell the user to complete Drive authorization.
- If MCP connect times out, diagnose stale local MCP listeners and stale controlled browser state before retrying.
- If the same error appears twice, stop and evaluate distinct fixes before another retry.

## Testing

Automated tests should cover:

- Chrome profile metadata parsing.
- Interactive wizard choice handling.
- Drive and temporary workspace path resolution.
- Generated setup cell defaults.
- XDG persistence link generation.
- Temporary mode warning requirement.
- Existing OpenCode mode remains available as an explicit option.

Manual validation should cover:

- Profile selection using a signed-in profile.
- MCP auto-connect without clicking the Colab dialog.
- Native shell terminal opens locally.
- A file created in the Drive workspace is visible after reconnect.
- `.config` and `.local/share` state survive reconnect.
- Temporary `/content` mode requires explicit confirmation.

## Known Limits

- Colab runtime lifetime and idle termination are controlled by Colab.
- Active tmux or terminal processes do not survive VM deletion.
- Drive is persistent but not ideal for heavy cache or many tiny write operations.
- Proot distro mode is possible but deferred until the native shell workflow is stable.

## Confidence

Confidence for the core workflow is 85%.

The remaining risks are Colab-managed runtime lifecycle, Drive mount authorization, profile authentication drift, and Drive performance for write-heavy workloads. The design mitigates these by treating Colab as disposable compute, making Drive the durable store, using a copied browser profile for controlled auth, and keeping heavy caches temporary by default.
