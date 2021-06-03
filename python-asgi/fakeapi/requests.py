from urllib.parse import parse_qs


class Request:
    charset = "utf-8"

    def __init__(self, scope, receive, send) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send
        self.init_headers(scope)

    def init_headers(self, scope):
        self.headers = {
            k.decode("latin-1").lower(): v.decode("latin-1")
            for k, v in scope["headers"]
        }

    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            event = await self.receive()
            self._body = event["body"]
            more_body = event.get("more_body", False)
            while more_body:
                event = await self.receive()
                self._body += event["body"]
                more_body = event.get("more_body", False)

        return self._body

    async def form(self) -> dict:
        if self.headers.get("content-type") == "application/x-www-form-urlencoded":
            body = await self.body()
            qs = parse_qs(body.decode(self.charset))
            return {k: v[0] for k, v in qs.items() if v}

        return {}

    @property
    def query_params(self) -> dict:
        qs = parse_qs(self.scope["query_string"].decode("latin-1"))
        return {k: v[0] if len(v) == 1 else v for k, v in qs.items()}
