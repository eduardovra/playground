import json
from typing import Any


class Response:
    media_type = None
    charset = "utf-8"

    def __init__(
        self,
        body: Any,
        status_code: int = 200,
        media_type: str = None,
        headers: dict = {},
    ) -> None:
        self.body = self.render(body)
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.init_headers(headers)

    async def __call__(self, scope, receive, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        await send({"type": "http.response.body", "body": self.body})

    def init_headers(self, headers):
        self.raw_headers = [
            (b"Content-Type", self.media_type.encode(self.charset)),
            (b"Content-Length", f"{len(self.body)}".encode(self.charset)),
        ]
        # TODO include application headers

    def render(self, content: Any) -> bytes:
        return content.encode(self.charset)


class HTMLResponse(Response):
    media_type = "text/html"


class PlainTextResponse(Response):
    media_type = "text/plain"


class JSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(content).encode(self.charset)
