from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import parse_qs

from .responses import HTMLResponse


@dataclass
class Route:
    path: str
    allowed_methods: list
    func: Callable


class FastAPI:
    def __init__(self) -> None:
        self.routes: list[Route] = []

    async def __call__(self, scope, receive, send) -> None:
        # Parse headers
        req_headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}

        # Fetch body
        kwargs = {}
        resp_body = b""
        if req_headers.get("content-length", 0):
            event = await receive()
            resp_body += event["body"]
            more_body = event.get("more_body", False)
            while more_body:
                event = await receive()
                resp_body += event["body"]
                more_body = event.get("more_body", False)

            if req_headers.get("content-type") == "application/x-www-form-urlencoded":
                qs = parse_qs(resp_body.decode())
                kwargs = {k: v[0] for k, v in qs.items() if v}

        # Find a matching route
        for route in self.routes:
            if route.path == scope["path"]:
                if scope["method"] not in route.allowed_methods:
                    raise Exception(
                        f"Method {scope['method']} not allowed for {scope['path']}"
                    )

                # Call handling function
                response = await route.func(**kwargs)

                # Send response back to ASGI server
                # Header first
                headers = self.build_resp_header(response)
                await send(headers)
                # Then the body
                body = self.build_resp_body(response)
                await send(body)

                return
        else:
            raise Exception(f"No route was found for path {scope['path']}")

    def build_resp_header(self, response: HTMLResponse) -> dict:
        return {
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"Content-Type", b"text/html; charset=UTF-8"),
                (b"Content-Length", f"{len(response.body.encode())}".encode()),
            ],
        }

    def build_resp_body(self, response: HTMLResponse) -> dict:
        return {"type": "http.response.body", "body": response.body.encode()}

    def get(self, path: str):
        def wrapped_get(func: Callable):
            self.routes.append(Route(path, ["GET"], func))
            return func

        return wrapped_get

    def post(self, path: str):
        def decorator_post(func: Callable):
            self.routes.append(Route(path, ["POST"], func))
            return func

        return decorator_post


class Form:
    def __init__(self, anything: Any) -> None:
        pass
