# Problem: English conversion patch context mismatch

## Exact error

```text
apply_patch verification failed: Failed to find expected lines in /home/astra/codex/Google-Colab/better_colab_MCP/tests/session_test.py:
                "source": ["print('\\u4f60\\u597d')\n"],
                "outputs": [
                    {"output_type": "stream", "name": "stdout", "text": ["\\u4f60\\u597d\n"]}
                ],
            },
        ]
        notebook = session.ColabRuntimeManagementTool._notebook_document(
            cells, name="\\u6d4b\\u8bd5.ipynb"
        )

        assert notebook["metadata"]["colab"]["name"] == "\\u6d4b\\u8bd5.ipynb"
        assert notebook["cells"][0]["metadata"] == {"custom": "\\u503c"}
        assert notebook["cells"][1]["outputs"][0]["text"] == ["\\u4f60\\u597d\n"]
```

## Reproduction steps

1. Work in `/home/astra/codex/Google-Colab/better_colab_MCP`.
2. Apply a broad patch converting non-English strings across `session.py`, `tests/session_test.py`, and docs.

## Environment

- Repository: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Branch: `master`
- Files being edited: `src/colab_mcp/session.py`, `tests/session_test.py`, `docs/TROUBLESHOOTING.md`, `docs/TOOLS.md`

## First hypothesis

The patch used test context that does not match the current formatting. Smaller replacements anchored to exact current lines should apply cleanly.
