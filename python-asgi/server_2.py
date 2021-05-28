import asyncio
from http import HTTPStatus

from main import app

# async def app(scope, receive, send)
scope = {
    "type": "http",
    "http_version": "1.1",
    "method": "GET",
    "scheme": "http",
    "path": "/",
    "query_string": b"search=red+blue&maximum_price=20",
    "headers": [(b"host", b"www.example.org"), (b"accept", b"application/json")],
    "client": ("134.56.78.4", 1453),
    "server": ("www.example.org", 443),
}

"""
GET /favicon.ico HTTP/1.1
Host: 127.0.0.1:8000
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"
sec-ch-ua-mobile: ?0
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36
Accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: no-cors
Sec-Fetch-Dest: image
Referer: http://127.0.0.1:8000/
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9,pt-BR;q=0.8,pt;q=0.7
Cookie: _ga=GA1.1.282284823.1618000024; _ga_ZQGY85X7XW=GS1.1.1618495848.1.1.1618496059.0
"""


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    header = await reader.readline()
    method, path, protocol = header.decode().rstrip().split(" ", 3)
    __, http_version = protocol.split("/")

    headers = []
    while True:
        header = await reader.readline()
        header = header.decode().rstrip()
        if not header:
            break
        key, value = header.split(": ", 1)
        headers.append((key.encode(), value.encode()))

    sock = writer.get_extra_info("socket")
    client = sock.getpeername()
    server = sock.getsockname()
    scope = {
        "type": "http",
        "http_version": http_version,
        "method": method,
        "scheme": "http",
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": client,
        "server": server,
    }

    async def receive():
        pass

    async def send(data):
        if data["type"] == "http.response.start":
            status = HTTPStatus(data["status"])

            status_line = f"{protocol} {status.value} {status.phrase}\r\n".encode()
            headers = []
            for header in data["headers"]:
                key, value = header[0].decode(), header[1].decode()
                headers.append(f"{key}: {value}\r\n".encode())

            writer.writelines([status_line, *headers, "\r\n".encode()])
            await writer.drain()
        elif data["type"] == "http.response.body":
            writer.writelines([data["body"], "\r\n".encode()])
            await writer.drain()
        else:
            raise Exception("Not implemented")

    await app(scope, receive, send)

    writer.close()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8000)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
