# Output Query Main Not Called

Problem file: [../problems/2026-06-07-output-query-main-not-called.md](../problems/2026-06-07-output-query-main-not-called.md)

## What Failed

An inline Python MCP query defined `async def main()` but did not call it, so no cells or outputs were queried.

## What Worked

Add `asyncio.run(main())` at the end of the inline Python script.

## Why It Worked

Defining an async function only creates a coroutine function. `asyncio.run(main())` actually executes it in an event loop.

## Commands Run

```bash
PYTHONPATH=scripts uv run python - <<'PY'
import asyncio

async def main():
    ...

asyncio.run(main())
PY
```
