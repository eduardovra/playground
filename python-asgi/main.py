from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.requests import Request


app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Hello world</title>
            </head>
            <body>
                <h1>Hello world</h1>
            </body>
        </html>
    """
    )
