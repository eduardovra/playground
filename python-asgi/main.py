from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request


app = FastAPI()


@app.get("/")
async def get(wsgi="Flask", asgi="FastAPI"):
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Hello world</title>
            </head>
            <body>
                <h1>Hello world</h1>
                <ul>
                    <li>wsgi={wsgi}</li>
                    <li>asgi={asgi}</li>
                </ul>
            </body>
        </html>
    """
    )
