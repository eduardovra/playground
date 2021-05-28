# Added form post support

import asyncio
from http import HTTPStatus
from urllib.parse import urlparse

from main import app


def build_scope(request_line: bytes) -> dict:
    request = request_line.decode().rstrip()
    print(request)

    method, path, protocol = request.split(" ", 3)
    url = urlparse(path)
    __, http_version = protocol.split("/")

    return {
        "type": "http",
        "http_version": http_version,
        "method": method,
        "scheme": "http",
        "path": url.path,
        "query_string": url.query.encode(),
    }


async def read_headers(reader: asyncio.StreamReader) -> dict[str, str]:
    headers = {}

    while True:
        header_line = await reader.readline()
        header = header_line.decode().rstrip().lower()
        if not header:
            break
        key, value = header.split(": ", 1)
        headers[key] = value

    return headers


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    request_line = await reader.readline()
    # Check if connection was closed by the client
    if request_line == b"" or reader.at_eof():
        return

    scope = build_scope(request_line)
    raw_headers = await read_headers(reader)
    content_length = int(raw_headers.get("content-length", 0))
    scope["headers"] = [(k.encode(), v.encode()) for k, v in raw_headers.items()]

    async def receive() -> dict:
        return {
            "type": "http.request",
            "body": await reader.read(content_length),
            "more_body": False,
        }

    async def send(data):
        if data["type"] == "http.response.start":
            protocol = "HTTP/1.1"
            status = HTTPStatus(data["status"])

            status_line = f"{protocol} {status.value} {status.phrase}"
            headers = [status_line]
            for header in data["headers"]:
                key, value = header[0].decode(), header[1].decode()
                headers.append(f"{key}: {value}")
            headers.append("")

            writer.writelines([f"{line}\r\n".encode() for line in headers])
            await writer.drain()
        elif data["type"] == "http.response.body":
            writer.writelines([data["body"], "\r\n".encode()])
            await writer.drain()
        else:
            raise Exception(f"Type not implemented {data['type']}")

    await app(scope, receive, send)

    writer.close()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8000)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    print("Listening on http://127.0.0.1:8000")
    asyncio.run(main())
