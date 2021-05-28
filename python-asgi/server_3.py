# Implemented query_string support

import asyncio
from http import HTTPStatus
from urllib.parse import urlparse

from main import app


async def build_scope(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter
) -> dict:
    request_line = await reader.readline()
    method, path, protocol = request_line.decode().rstrip().split(" ", 3)
    url = urlparse(path)
    path = url.path
    query_string = url.query.encode()
    __, http_version = protocol.split("/")

    headers = []
    while True:
        header_line = await reader.readline()
        header = header_line.decode().rstrip()
        if not header:
            break
        key, value = header.split(": ", 1)
        headers.append((key.encode(), value.encode()))

    sock = writer.get_extra_info("socket")

    return {
        "type": "http",
        "http_version": http_version,
        "method": method,
        "scheme": "http",
        "path": path,
        "query_string": query_string,
        "headers": [],
        "client": sock.getpeername(),
        "server": sock.getsockname(),
    }


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    async def receive():
        pass

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
            raise Exception("Not implemented")

    scope = await build_scope(reader, writer)
    await app(scope, receive, send)

    writer.close()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8000)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
