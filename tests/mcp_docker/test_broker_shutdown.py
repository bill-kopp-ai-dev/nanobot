"""Bounded drain behavior for broker HTTP requests during shutdown."""

from __future__ import annotations

import http.server
import threading
import urllib.request

from nanobot.mcp_docker.broker import DrainingThreadingHTTPServer


def test_server_drains_an_active_request_after_shutdown_stops_accepting() -> None:
    request_started = threading.Event()
    finish_request = threading.Event()
    response: list[int] = []

    class BlockingHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            request_started.set()
            assert finish_request.wait(2)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"complete")

        def log_message(self, _format: str, *_args: object) -> None:
            pass

    server = DrainingThreadingHTTPServer(("127.0.0.1", 0), BlockingHandler)
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()

    def request() -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{server.server_port}/", timeout=3) as result:
            response.append(result.status)
            assert result.read() == b"complete"

    client = threading.Thread(target=request, daemon=True)
    client.start()
    try:
        assert request_started.wait(2)
        server.shutdown()
        assert not server.wait_for_drain(0.01)
        finish_request.set()
        assert server.wait_for_drain(2)
        client.join(2)
        assert not client.is_alive()
        assert response == [200]
    finally:
        finish_request.set()
        server.server_close()
        serving.join(2)
