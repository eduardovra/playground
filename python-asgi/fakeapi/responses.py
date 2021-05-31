from dataclasses import dataclass


@dataclass
class HTMLResponse:
    body: str
    status_code: int = 200
    media_type: str = "text/html"
