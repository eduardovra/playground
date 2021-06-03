from typing import Any, Callable

from .routing import Router


class FastAPI:
    def __init__(self) -> None:
        self.router = Router()

    async def __call__(self, scope, receive, send) -> None:
        await self.router(scope, receive, send)

    def route(self, path: str, methods: list[str]):
        def decorator(func: Callable):
            self.router.add_route(path, methods, func)
            return func

        return decorator

    def get(self, path: str) -> Callable:
        return self.route(path, methods=["GET"])

    def post(self, path: str) -> Callable:
        return self.route(path, methods=["POST"])


class Form:
    def __init__(self, anything: Any) -> None:
        pass
