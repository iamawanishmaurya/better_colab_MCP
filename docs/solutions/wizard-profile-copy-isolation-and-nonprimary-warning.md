# Solution: Wizard profile-copy isolation and non-primary warning

Links back to:

- [Wizard Default profile login required](../problems/2026-06-07-wizard-default-profile-login-required.md)
- [Drive launcher reused profile login required](../problems/2026-06-07-drive-launcher-reused-profile-login-required.md)

## What Failed

The wizard let the user select Chrome profile `Default`, which has account metadata but is not marked as Chrome's primary signed-in account. It also reused the shared copied profile directory:

```text
/tmp/colab-mcp-drive-terminal-profile-copy
```

That copied profile reached Colab as logged out. MCP connected, but runtime connection failed with `loginRequired: True`.

## Distinct Solutions Evaluated

1. Always force `Profile 32`.
   - Benefit: it matches the currently known primary signed-in profile.
   - Trade-off: too machine-specific and blocks users who legitimately want another authenticated profile.

2. Always add `--refresh-profile-copy`.
   - Benefit: avoids preserving an old anonymous copied profile.
   - Trade-off: can still fail for non-primary profiles and can wipe a dedicated copied profile that the user signed into manually.

3. Make copied profile directories unique per selected Chrome profile.
   - Benefit: prevents `Default`, `Profile 32`, and other source profiles from sharing the same stale copied profile state.
   - Trade-off: first run for each profile may need a fresh copy or sign-in.

4. Warn on non-primary profile selection and default back to the primary profile unless the user explicitly confirms.
   - Benefit: prevents accidental selection of profiles likely to open Colab logged out.
   - Trade-off: adds one prompt when the user intentionally chooses a non-primary profile.

5. Require manual sign-in in the controlled copied browser.
   - Benefit: can work even when Chrome cookies cannot be copied cleanly.
   - Trade-off: less automatic and still needs profile-copy isolation so that sign-in is preserved for the right source profile.

## What Worked

Combine options 3 and 4:

- Derive the default copied profile directory from the selected profile directory.
- Keep user-provided `--profile-copy-dir` as an exact override.
- Warn when an interactive user selects a profile that is not marked as the primary signed-in Chrome profile.
- If a primary profile exists, pressing Enter selects the primary profile; typing `use-non-primary` continues with the selected non-primary profile.

## Why It Worked

Profile-copy isolation prevents stale or wrong-profile browser state from leaking between wizard runs. The non-primary warning handles the specific `Default` profile case seen here: it has account metadata for `canbehumanagain@gmail.com` / `nothumanatall`, but Colab still showed `Sign in` in the controlled copied profile. Steering the user to the primary profile avoids the known runtime blocker without hard-coding a local profile name.

## Commands Run

```bash
uv run pytest tests/drive_terminal_wizard_test.py -q
uv run colab-drive-terminal --profile 'Profile 32' --workspace drive --project smoke --dry-run
uv run colab-drive-terminal --profile Default --workspace drive --project smoke --dry-run
uv run pytest -q
printf '2\n\n1\n' | uv run colab-drive-terminal --dry-run
```

Results:

```text
9 passed
91 passed, 1 warning
Profile 32 dry-run: --browser-profile-copy-dir /tmp/colab-mcp-drive-terminal-profile-copy-profile-32
Default dry-run: --browser-profile-copy-dir /tmp/colab-mcp-drive-terminal-profile-copy-default
Interactive Default selection with Enter fell back to --browser-profile Profile 32
```
