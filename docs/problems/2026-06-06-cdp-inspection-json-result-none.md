# CDP Inspection JSON Result None

## Exact Error

A local diagnostic script for inspecting Colab iframe/proxy metadata failed while parsing the CDP result:

```text
TypeError: the JSON object must be str, bytes or bytearray, not NoneType
```

## Reproduction Steps

1. Queried the Colab page over CDP on port `9458`.
2. Expected `Runtime.evaluate` to return a string value.
3. Called `json.loads(val)` where `val` was `None`.

## Environment

- Repo: `/home/astra/codex/Google-Colab/better_colab_MCP`
- CDP port: `9458`
- Page: `https://colab.research.google.com/notebooks/empty.ipynb`

## First Hypothesis

The evaluated JavaScript either threw or returned an unserializable value. The diagnostic should print the full CDP response and include exception details instead of assuming `result.value` exists.
