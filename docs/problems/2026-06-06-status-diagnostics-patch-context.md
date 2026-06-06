# Problem: status diagnostics patch context mismatch

## Exact error

```text
apply_patch verification failed: Failed to find expected lines in /home/astra/codex/Google-Colab/better_colab_MCP/src/colab_mcp/session.py:
        if self.name == "get_connection_info":
            info = dict(self._proxy_client.wss.connection_info())
            info["connected"] = self._proxy_client.is_connected()
            text = json.dumps(info, ensure_ascii=False)
            return ToolResult(
```

## Reproduction steps

1. Work in `/home/astra/codex/Google-Colab/better_colab_MCP`.
2. Apply a combined patch that adds `_browser_diagnostics()` and edits the `get_connection_info` branch in `src/colab_mcp/session.py`.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- File being edited: `src/colab_mcp/session.py`

## First hypothesis

The combined patch used stale surrounding context after earlier browser-helper edits. A smaller patch anchored around current nearby lines should apply cleanly.
