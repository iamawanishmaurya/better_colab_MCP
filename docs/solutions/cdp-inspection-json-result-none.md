# Solution: CDP Inspection JSON Result None

Links back to: `docs/problems/2026-06-06-cdp-inspection-json-result-none.md`

## What Failed

The diagnostic script assumed `Runtime.evaluate` returned `result.value` as a string.

## What Worked

Rerun the diagnostic with explicit CDP response printing and safer JavaScript expressions instead of immediately calling `json.loads()` on a possibly missing value.

## Why It Worked

CDP reports JavaScript exceptions and unserializable values differently from normal string return values. Printing the response first prevents a local parser error from hiding the browser-side cause.

## Commands Run

```bash
python - <<'PY'
# queried http://127.0.0.1:9458/json/list and Runtime.evaluate
PY
```
