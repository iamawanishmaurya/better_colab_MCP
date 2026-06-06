# Opencode Localhost Gzip Double Decode

## Exact Error

After forwarding the Colab runtime proxy cookie, the localhost smoke reached ttyd but failed while reading the response:

```text
aiohttp.http_exceptions.ContentEncodingError: 400, message:
  Can not decode content-encoding: gzip

aiohttp.client_exceptions.ClientPayloadError: 400, message:
  Can not decode content-encoding: gzip
```

The run also reported an unclosed local proxy client session because the smoke exception happened before cleanup:

```text
Unclosed client session
Unclosed connector
```

## Reproduction Steps

1. Ran the Opencode localhost smoke command after adding CDP cookie forwarding.
2. The script connected MCP, connected runtime, started ttyd on Colab port `7681`, extracted the proxy URL, extracted `colab-runtime-proxy-token`, and started local `http://127.0.0.1:8765`.
3. The smoke request failed while decoding the local proxy response.

## Environment

- Repo: `/home/astra/codex/Google-Colab/better_colab_MCP`
- Localhost port: `8765`
- CDP port: `9458`
- Colab ttyd port: `7681`
- aiohttp: `3.14.0`

## First Hypothesis

The upstream proxy `ClientSession` auto-decompressed ttyd's gzip response but the local proxy forwarded the original `Content-Encoding: gzip` header with the already-decoded body. The fix is to preserve upstream bytes by disabling auto-decompression in the proxy client session, and to clean up the proxy runner if smoke testing raises.
