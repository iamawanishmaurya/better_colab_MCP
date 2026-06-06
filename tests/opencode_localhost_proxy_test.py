import sys
from pathlib import Path

from aiohttp import ClientSession, WSMsgType, web
from multidict import CIMultiDict
import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from colab_opencode_localhost import (  # noqa: E402
    make_proxy_app,
    requested_websocket_protocols,
)


async def start_app(app: web.Application) -> tuple[web.AppRunner, str]:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    sockets = site._server.sockets
    assert sockets
    port = sockets[0].getsockname()[1]
    return runner, f"http://127.0.0.1:{port}"


@pytest.mark.asyncio
async def test_requested_websocket_protocols_deduplicates_header_values():
    request = type(
        "Request",
        (),
        {"headers": CIMultiDict({"Sec-WebSocket-Protocol": "tty, tty, other"})},
    )()

    assert requested_websocket_protocols(request) == ("tty", "other")


@pytest.mark.asyncio
async def test_proxy_websocket_preserves_tty_subprotocol():
    remote_protocols: list[str | None] = []

    async def remote_ws(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(protocols=("tty",))
        await ws.prepare(request)
        remote_protocols.append(ws.ws_protocol)
        await ws.send_str(f"remote-ready:{ws.ws_protocol}")
        async for message in ws:
            if message.type == WSMsgType.TEXT:
                await ws.send_str(f"echo:{message.data}")
        return ws

    remote_app = web.Application()
    remote_app.router.add_get("/ws", remote_ws)
    remote_runner, remote_base = await start_app(remote_app)

    local_runner = None
    try:
        local_app = await make_proxy_app(remote_base, {})
        local_runner, local_base = await start_app(local_app)

        async with ClientSession() as session:
            async with session.ws_connect(f"{local_base}/ws", protocols=("tty",)) as ws:
                assert ws.protocol == "tty"

                ready = await ws.receive(timeout=3)
                assert ready.type == WSMsgType.TEXT
                assert ready.data == "remote-ready:tty"
                assert remote_protocols == ["tty"]

                await ws.send_str("ping")
                echo = await ws.receive(timeout=3)
                assert echo.type == WSMsgType.TEXT
                assert echo.data == "echo:ping"
    finally:
        if local_runner is not None:
            await local_runner.cleanup()
        await remote_runner.cleanup()
