# API Conventions

This fork keeps the public MCP tool names compatible with Colab-style and upstream tool names, while Python internals use normal `snake_case`.

## Public MCP Tools

- Tool names are stable external API. Existing names such as `run_code_cell`, `set_env_vars`, and `download_notebook` should not be renamed casually.
- Input schemas may keep browser/Colab argument casing when compatibility requires it, for example `cellId`, `cellIds`, `includeOutputs`, `timeoutSeconds`, and `maxBytes`.
- New Python-runtime tools should prefer `snake_case` tool names and Colab-compatible argument names only where that makes agent prompts or upstream parity clearer.

## Internal Python

- Functions, local variables, helper names, and test fixtures use `snake_case`.
- Schema dictionaries may contain camelCase keys because they are external MCP contracts.
- Tool implementations should normalize arguments at the boundary, then use internal snake_case variables.
- Structured results should include `ok`, `status`, `error`, and `warnings` when a tool can partially succeed or expose actionable diagnostics.

## Result Shape

- Prefer structured content over text parsing for automation.
- Use `maxBytes` or equivalent truncation controls for potentially large output.
- Redact secret-looking values in text output; structured metadata can keep safe booleans, names, sizes, and hashes.
- Return per-item results for batch operations instead of failing the entire call unless the input schema itself is invalid.
