"""The real SDK must emit a cancellation notification, not only drop its waiter."""

import asyncio

import anyio
import pytest

from nanobot.agent.tools.mcp_session import CancellableClientSession


@pytest.mark.asyncio
async def test_cancelled_sdk_request_notifies_exact_request_id():
    incoming, read = anyio.create_memory_object_stream(4)
    write, outgoing = anyio.create_memory_object_stream(4)
    async with incoming, outgoing, CancellableClientSession(read, write) as session:
        call = asyncio.create_task(session.call_tool("research_deep", {"query": "fixture"}))
        request = await outgoing.receive()
        call.cancel()
        with pytest.raises(asyncio.CancelledError):
            await call
        notification = await asyncio.wait_for(outgoing.receive(), 1)
        assert notification.message.root.method == "notifications/cancelled"
        assert notification.message.root.params["requestId"] == request.message.root.id
