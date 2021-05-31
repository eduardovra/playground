from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.parse import parse_qs

from .responses import HTMLResponse


@dataclass
class Route:
    path: str
    allowed_methods: list
    func: Callable

    def match(self, path: str, method: str) -> Optional[dict]:
        matching = {}

        segments = zip(self.path.split("/"), path.split("/"))
        for seg_route, seg_path in segments:
            if seg_route == seg_path:
                continue
            elif seg_route and seg_route[0] == "{" and seg_route[-1] == "}":
                matching[seg_route[1:-1]] = seg_path
            else:
                return None

        if method not in self.allowed_methods:
            raise Exception(f"Method {method} not allowed for {path}")

        return matching


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
        func, path_parameters = self.find_matching_route(scope["path"], scope["method"])
        if func and path_parameters:
            # Path parameters
            kwargs.update(path_parameters)
            # Call user-defined handling function
            response = await func(**kwargs)

            # Send response back to ASGI server
            headers = self.build_resp_header(response)
            await send(headers)
            body = self.build_resp_body(response)
            await send(body)
        else:
            response = HTMLResponse("Not Found", 404)
            headers = self.build_resp_header(response)
            await send(headers)
            body = self.build_resp_body(response)
            await send(body)

    def find_matching_route(
        self, path: str, method: str
    ) -> tuple[Optional[Callable], Optional[dict]]:
        for route in self.routes:
            path_parameters = route.match(path, method)
            if isinstance(path_parameters, dict):
                return route.func, path_parameters

        return None, None

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

    def get(self, path: str) -> Callable:
        """GET decorator"""
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> Callable:
        """POST decorator"""
        return self.route(path, methods=["POST"])


class Form:
    def __init__(self, anything: Any) -> None:
        pass
