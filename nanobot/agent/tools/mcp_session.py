"""MCP SDK session with protocol cancellation for abandoned requests."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TypeVar

import anyio
from mcp import ClientSession, McpError, types
from mcp.shared.message import MessageMetadata
from mcp.shared.session import ProgressFnT
from pydantic import BaseModel

_Result = TypeVar("_Result", bound=BaseModel)


class CancellableClientSession(ClientSession):
    async def send_request(
        self,
        request: types.ClientRequest,
        result_type: type[_Result],
        request_read_timeout_seconds: timedelta | None = None,
        metadata: MessageMetadata = None,
        progress_callback: ProgressFnT | None = None,
    ) -> _Result:
        # The pinned SDK reserves this ID synchronously at the start of
        # super().send_request, before its first await. Concurrent calls cannot
        # steal it. Keep this SDK boundary covered by the real-pipe regression.
        request_id = self._request_id
        try:
            return await super().send_request(
                request, result_type, request_read_timeout_seconds, metadata, progress_callback,
            )
        except (asyncio.CancelledError, McpError) as exc:
            if isinstance(exc, McpError) and exc.error.code != 408:
                raise
            if request.root.method != "initialize":
                # The SDK removes its response waiter but does not notify the
                # server. Sending must survive the caller's cancellation scope.
                with anyio.CancelScope(shield=True):
                    try:
                        await asyncio.wait_for(self.send_notification(types.ClientNotification(
                            types.CancelledNotification(params=types.CancelledNotificationParams(
                                requestId=request_id, reason="Percival caller stopped waiting",
                            )),
                        )), timeout=1)
                    except (Exception, asyncio.CancelledError):
                        pass  # Transport loss stays an ambiguous outcome; never replay.
            raise
