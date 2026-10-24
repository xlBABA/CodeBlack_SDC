"""A local, in-process OpenAI-compatible chat-completions server for CV
tests. Records every request (path, Authorization header, JSON body) and
answers with a canned completion, optionally after a delay. Binds to
127.0.0.1 on a free port; never reaches the network."""
from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator


class FakeLlmServer:
    def __init__(
        self, content: str, delay_seconds: float = 0.0, status: int = 200, finish_reason: str = "stop"
    ) -> None:
        self.content = content
        self.delay_seconds = delay_seconds
        self.status = status
        self.finish_reason = finish_reason
        self.requests: list[dict] = []
        server = self

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, *args) -> None:  # keep test output quiet
                pass

            def do_POST(self) -> None:
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                server.requests.append(
                    {"path": self.path, "authorization": self.headers.get("Authorization"), "body": body}
                )
                if server.delay_seconds:
                    time.sleep(server.delay_seconds)
                choice = {"message": {"role": "assistant", "content": server.content}, "finish_reason": server.finish_reason}
                reply = json.dumps({"choices": [choice]})
                data = reply.encode()
                self.send_response(server.status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._httpd.daemon_threads = True
        self.base_url = f"http://127.0.0.1:{self._httpd.server_address[1]}/v1"

    def start(self) -> None:
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()


@contextmanager
def fake_llm_server(
    content: str, delay_seconds: float = 0.0, status: int = 200, finish_reason: str = "stop"
) -> Iterator[FakeLlmServer]:
    server = FakeLlmServer(content, delay_seconds, status, finish_reason)
    server.start()
    try:
        yield server
    finally:
        server.stop()
