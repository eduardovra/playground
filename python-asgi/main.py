from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse


app = FastAPI()


@app.get("/")
async def get():
    return HTMLResponse(
        f"""
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


@app.post("/post")
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
