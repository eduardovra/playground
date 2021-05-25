import asyncio
from datetime import datetime

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import websockets
import psutil

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    processes = psutil.process_iter()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "server_time": datetime.now(), "processes": processes},
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        # data = await websocket.receive_text()
        await asyncio.sleep(1)
        processes = psutil.process_iter()
        html = templates.TemplateResponse(
            "_stream.html",
            {"request": None, "server_time": datetime.now(), "processes": processes},
        )
        try:
            await websocket.send_text(html.body.decode(html.charset))
        except websockets.exceptions.ConnectionClosedOK:
            break
