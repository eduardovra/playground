# from fastapi import FastAPI, Form
# from fastapi.responses import HTMLResponse

from fakeapi import FastAPI, Form
from fakeapi.responses import HTMLResponse


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
