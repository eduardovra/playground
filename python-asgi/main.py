from fastapi import FastAPI, WebSocket, Form
from fastapi.responses import HTMLResponse

# from fakeapi import FastAPI, Form
# from fakeapi.responses import HTMLResponse


app = FastAPI()


@app.route("/", methods=["GET"])
async def get():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Hello world</title>
            </head>
            <body>
                <h1>Hello world</h1>
                <form method="POST" action="/post">
                    <input type="text" name="favorite"
                        placeholder="Your favorite framework?" />
                    <button>Submit</button>
                </form>
            </body>
        </html>
    """
    )


@app.route("/post", methods=["POST"])
async def post(favorite: str = Form(...)):
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>Hello world</title>
            </head>
            <body>
                <h1>Your favorite framework is {favorite}</h1>
            </body>
        </html>
    """
    )


@app.route("/query-string", methods=["GET"])
async def query_string(required: str, optional: int = 5):
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
            <head><title>Query string</title></head>
            <body>
                <p>required: {required}</p>
                <p>optional: {optional}</p>
            </body>
        </html>
    """
    )


@app.get("/path-parameter/{item_id}")
async def path_parameter(item_id: int):
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html>
            <head><title>Path parameter</title></head>
            <body><p>item_id: {item_id}</p></body>
        </html>
    """
    )


@app.get("/websocket-base")
async def websocket_base():
    html = """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Chat</title>
                </head>
                <body>
                    <h1>WebSocket Chat</h1>
                    <form action="" onsubmit="sendMessage(event)">
                        <input type="text" id="messageText" autocomplete="off"/>
                        <button>Send</button>
                    </form>
                    <ul id='messages'>
                    </ul>
                    <script>
                        var ws = new WebSocket("ws://localhost:8000/ws");
                        ws.onmessage = function(event) {
                            var messages = document.getElementById('messages')
                            var message = document.createElement('li')
                            var content = document.createTextNode(event.data)
                            message.appendChild(content)
                            messages.appendChild(message)
                        };
                        function sendMessage(event) {
                            var input = document.getElementById("messageText")
                            ws.send(input.value)
                            input.value = ''
                            event.preventDefault()
                        }
                    </script>
                </body>
            </html>
    """
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
