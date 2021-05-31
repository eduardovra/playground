from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import parse_qs

from .responses import HTMLResponse


@dataclass
class Route:
    path: str
    allowed_methods: list
    func: Callable

    def match(self, path: str, method: str) -> bool:
        if path == self.path:
            if method in self.allowed_methods:
                return True
            raise Exception(f"Method {method} not allowed for {path}")

        return False


class FastAPI:
    def __init__(self) -> None:
        self.routes: list[Route] = []

    async def __call__(self, scope, receive, send) -> None:
        # Parse query string
        qs = parse_qs(scope["query_string"].decode())
        kwargs = {}
        for k, v in qs.items():
            kwargs[k] = v[0] if len(v) == 1 else v

        # Parse headers
        req_headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}

        # Fetch body
        if req_headers.get("content-length", 0):
            event = await receive()
            resp_body = event["body"]
            more_body = event.get("more_body", False)
            while more_body:
                event = await receive()
                resp_body += event["body"]
                more_body = event.get("more_body", False)

            # Form post with url encoded format
            if req_headers.get("content-type") == "application/x-www-form-urlencoded":
                qs = parse_qs(resp_body.decode())
                kwargs.update({k: v[0] for k, v in qs.items() if v})

        # Find a matching route
        route = self.find_matching_route(scope["path"], scope["method"])
        if route:
            # Call user-defined handling function
            response = await route.func(**kwargs)

            # Send response back to ASGI server
            headers = self.build_resp_header(response)
            await send(headers)
            body = self.build_resp_body(response)
            await send(body)
        else:
            headers = self.build_resp_header(HTMLResponse("Not Found", 404))
            await send(headers)

    def find_matching_route(self, path: str, method: str) -> Optional[Route]:
        for route in self.routes:
            if route.match(path, method):
                return route

        return None

    def build_resp_header(self, response: HTMLResponse) -> dict:
        return {
            "type": "http.response.start",
            "status": response.status_code,
            "headers": [
                (b"Content-Type", response.media_type.encode()),
                (b"Content-Length", f"{len(response.body.encode())}".encode()),
            ],
        }

    def build_resp_body(self, response: HTMLResponse) -> dict:
        return {"type": "http.response.body", "body": response.body.encode()}

    def route(self, path: str, methods: list[str]):
        """Route decorator"""

        def wrapped_route(func: Callable):
            self.routes.append(Route(path, methods, func))
            return func

        return wrapped_route


class Form:
    def __init__(self, anything: Any) -> None:
        pass
