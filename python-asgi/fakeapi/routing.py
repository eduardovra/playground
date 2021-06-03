from enum import Enum
from typing import Any, Callable, Tuple

from .requests import Request
from .responses import JSONResponse, PlainTextResponse, Response


class Match(Enum):
    NONE = 0
    PARTIAL = 1
    FULL = 2


class Route:
    def __init__(self, path: str, methods: list[str], func: Callable) -> None:
        self.path = path
        self.methods = methods
        self.func = func

    def matches(self, scope: dict) -> Tuple[Match, dict]:
        path_params = {}
        segments = zip(self.path.split("/"), scope["path"].split("/"))

        for seg_route, seg_path in segments:
            if seg_route == seg_path:
                continue
            elif seg_route and seg_route[0] == "{" and seg_route[-1] == "}":
                path_params[seg_route[1:-1]] = seg_path
            else:
                return Match.NONE, path_params

        if scope["method"] not in self.methods:
            return Match.PARTIAL, path_params

        return Match.FULL, path_params

    async def handle(self, scope, receive, send) -> Response:
        request = Request(scope, receive, send)

        # Gather params for the user function
        query_params = request.query_params
        path_params = scope["path_params"]
        body_params = await request.form()

        # Call user defined function
        kwargs = query_params | path_params | body_params
        response = await self.func(**kwargs)

        # In case user function returns something like a dict
        if not isinstance(response, Response):
            response = JSONResponse(response)

        return response


class Router:
    def __init__(self) -> None:
        self.routes: list[Route] = []

    async def __call__(self, scope, receive, send) -> None:
        response = PlainTextResponse("Not Found", 404)  # type: Response

        # Find a matching route
        for route in self.routes:
            match, path_params = route.matches(scope)
            if match == Match.FULL:
                scope["path_params"] = path_params
                response = await route.handle(scope, receive, send)
                break
            elif match == Match.PARTIAL:
                response = PlainTextResponse("Method Not Allowed", 405)
                break

        # Send response back to ASGI server
        await response(scope, receive, send)

    def add_route(self, path: str, methods: list[str], func: Callable):
        route = Route(path, methods, func)
        self.routes.append(route)
