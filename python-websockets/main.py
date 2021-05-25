import asyncio
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import psutil

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    processes = psutil.process_iter()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "server_time": datetime.now(),
            "refresh_time": 1,
            "processes": processes,
        },
    )


async def processes(websocket, sort, order, refresh_time):
    while True:
        processes = [
            p.as_dict(attrs=("pid", "name", "status", "cpu_percent"))
            for p in psutil.process_iter()
        ]
        processes.sort(key=lambda p: p[sort], reverse=order == "desc")

        response = templates.TemplateResponse(
            "_stream.html",
            {
                "request": None,
                "server_time": datetime.now(),
                "sort": sort,
                "order": order,
                "refresh_time": refresh_time,
                "processes": processes,
            },
        )

        try:
            html = response.body.decode(response.charset)
            await websocket.send_text(html)
        except WebSocketDisconnect:
            break

        await asyncio.sleep(refresh_time)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    sort = "pid"
    order = "asc"
    refresh_time = 1
    coro = processes(websocket, sort, order, refresh_time)
    task = asyncio.create_task(coro)

    while True:
        try:
            data = await websocket.receive_json()
        except WebSocketDisconnect:
            break

        sort = data["sort"]
        order = data["order"]
        refresh_time = int(data["refresh"])
        task.cancel()
        coro = processes(websocket, sort, order, refresh_time)
        task = task = asyncio.create_task(coro)
