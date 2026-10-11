from __future__ import annotations

import asyncio
import errno
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.bus.queue import MessageBus
from nanobot.channels.websocket.runtime import WebSocketChannel


class _FakeSocket:
    def __init__(self) -> None:
        self.open = True

    def fileno(self) -> int:
        return 1 if self.open else -1

    def getsockopt(self, _level: int, _option: int) -> int:
        return int(self.open)


class _FakeServer:
    def __init__(self) -> None:
        self.socket = _FakeSocket()
        self.closed = False

    @property
    def sockets(self) -> tuple[_FakeSocket, ...]:
        return (self.socket,)

    def is_serving(self) -> bool:
        return not self.closed

    def close(self) -> None:
        self.closed = True
        self.socket.open = False

    async def wait_closed(self) -> None:
        return None


class _FakeRunner:
    def __init__(self, _app, **_kwargs) -> None:
        pass

    async def setup(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass


class _FakeSite:
    def __init__(self, runner, host, port, *, server, **_kwargs) -> None:
        self._server = server

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        self._server.close()


def _channel() -> WebSocketChannel:
    gateway = MagicMock()
    gateway.session_manager = None
    gateway.http.settings_routes.close = AsyncMock()
    gateway.http.remote_instances.close = AsyncMock()
    return WebSocketChannel(
        {"enabled": True, "allowFrom": ["*"]},
        MessageBus(),
        gateway=gateway,
    )


@pytest.mark.asyncio
async def test_websocket_does_not_report_running_before_bind_succeeds(monkeypatch) -> None:
    import nanobot.channels.websocket.runtime as runtime

    channel = _channel()
    channel.logger = MagicMock()
    bind_error = OSError(errno.EADDRINUSE, "address already in use")

    def fail_bind(*_args, **_kwargs):
        raise bind_error

    monkeypatch.setattr(runtime.web, "AppRunner", _FakeRunner)
    monkeypatch.setattr(runtime.web, "TCPSite", fail_bind)

    with pytest.raises(OSError) as exc_info:
        await channel.start()

    assert exc_info.value is bind_error
    assert channel.is_running is False
    assert not any(
        call.args and call.args[0] == "WebSocket server listening on {}"
        for call in channel.logger.info.call_args_list
    )


@pytest.mark.asyncio
async def test_websocket_restarts_only_its_listener_after_serving_socket_is_lost(
    monkeypatch,
) -> None:
    import nanobot.channels.websocket.runtime as runtime

    channel = _channel()
    first = _FakeServer()
    second = _FakeServer()
    servers = iter((first, second))
    bind_count = 0
    rebound = asyncio.Event()

    def bind(*_args, **kwargs):
        nonlocal bind_count
        bind_count += 1
        server = next(servers)
        if bind_count == 2:
            rebound.set()
        return _FakeSite(None, None, None, server=server, **kwargs)

    monkeypatch.setattr(runtime.web, "AppRunner", _FakeRunner)
    monkeypatch.setattr(runtime.web, "TCPSite", bind)
    monkeypatch.setattr(
        "nanobot.channels.websocket.runtime._LISTENER_CHECK_INTERVAL_S",
        0.01,
    )
    monkeypatch.setattr(
        "nanobot.channels.websocket.runtime._LISTENER_RESTART_BACKOFF_S",
        (0.05,),
    )

    start_task = asyncio.create_task(channel.start())
    try:
        for _ in range(20):
            if channel.is_running:
                break
            await asyncio.sleep(0)
        assert channel.is_running is True

        first.socket.open = False
        for _ in range(50):
            if not channel.is_running:
                break
            await asyncio.sleep(0.005)

        assert channel.is_running is False
        assert bind_count == 1
        await asyncio.wait_for(rebound.wait(), timeout=1)
        assert channel.is_running is True
        assert first.closed is True
    finally:
        await channel.stop()
        await start_task

    assert second.closed is True
