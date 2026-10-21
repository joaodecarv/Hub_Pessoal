"""hub:// -> in-memory ASGI bridge. No Qt here, so it is testable on its own.

`Bridge.handle` turns one request (method, path+query, headers, body) into a
response (status, headers, body): `/api/...` goes to the FastAPI app as a direct
ASGI call, anything else is a file from the frontend build. No socket is opened.

The app runs on a private asyncio loop in a background thread, started once by
`start()` together with the app's lifespan (which runs the data bootstrap).
`handle` blocks the calling thread until the response is complete, so callers
must not run it on the UI thread.
"""
import asyncio
import mimetypes
import threading
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote


@dataclass
class Response:
    status: int
    headers: list[tuple[str, str]]
    body: bytes

    def header(self, name: str) -> str | None:
        name = name.lower()
        return next((v for k, v in self.headers if k.lower() == name), None)


class Bridge:
    def __init__(self, app, static_dir):
        self._app = app
        self._static_dir = Path(static_dir).resolve()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="hub-asgi", daemon=True)
        self._lifespan_events: asyncio.Queue | None = None

    def start(self) -> None:
        """Start the loop and run the app's lifespan startup; raises if startup fails."""
        self._thread.start()
        self._run(self._lifespan_startup())

    def stop(self) -> None:
        if self._lifespan_events is not None:
            self._run(self._lifespan_shutdown())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
        self._loop.close()

    def handle(self, method: str, url: str, headers: dict[str, str], body: bytes) -> Response:
        path = url.partition("?")[0]
        if path == "/api" or path.startswith("/api/"):
            return self._run(self._call_app(method, url, headers, body))
        return self._static(unquote(path))

    def _static(self, path: str) -> Response:
        """A file from the build, or index.html for any other path (client-side routes)."""
        file = (self._static_dir / path.lstrip("/")).resolve()
        if not file.is_file() or not file.is_relative_to(self._static_dir):
            file = self._static_dir / "index.html"
        content_type = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        return Response(200, [("content-type", content_type)], file.read_bytes())

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    async def _call_app(self, method, url, headers, body) -> Response:
        path, _, query = url.partition("?")
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": "hub",
            "path": unquote(path),
            "raw_path": path.encode(),
            "root_path": "",
            "query_string": query.encode(),
            "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()],
            "client": None,
            "server": ("app", None),
        }
        request_sent = False
        response_done = asyncio.Event()

        async def receive():
            nonlocal request_sent
            if not request_sent:
                request_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            await response_done.wait()
            return {"type": "http.disconnect"}

        status, out_headers, chunks = 500, [], []

        async def send(message):
            nonlocal status, out_headers
            if message["type"] == "http.response.start":
                status = message["status"]
                out_headers = [(k.decode("latin-1"), v.decode("latin-1")) for k, v in message.get("headers", [])]
            elif message["type"] == "http.response.body":
                chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    response_done.set()

        try:
            await self._app(scope, receive, send)
        finally:
            response_done.set()
        return Response(status, out_headers, b"".join(chunks))

    async def _lifespan_startup(self):
        self._lifespan_events = asyncio.Queue()
        started = self._loop.create_future()
        self._lifespan_finished = self._loop.create_future()
        events = self._lifespan_events

        async def receive():
            return await events.get()

        async def send(message):
            kind = message["type"]
            if kind == "lifespan.startup.complete":
                started.set_result(None)
            elif kind == "lifespan.startup.failed":
                started.set_exception(RuntimeError(message.get("message", "lifespan startup failed")))
            elif kind in ("lifespan.shutdown.complete", "lifespan.shutdown.failed"):
                self._lifespan_finished.set_result(None)

        async def run():
            try:
                await self._app({"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}, receive, send)
            except BaseException as exc:
                if not started.done():
                    started.set_exception(exc)
            finally:
                if not self._lifespan_finished.done():
                    self._lifespan_finished.set_result(None)

        self._lifespan_task = asyncio.create_task(run())
        await events.put({"type": "lifespan.startup"})
        await started

    async def _lifespan_shutdown(self):
        await self._lifespan_events.put({"type": "lifespan.shutdown"})
        await self._lifespan_finished
