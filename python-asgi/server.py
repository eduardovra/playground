# Added websockets support

import asyncio
import struct
import base64
import hashlib
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
        header = header_line.decode("latin1").rstrip()
        if not header:
            break
        key, value = header.split(": ", 1)
        headers[key.lower()] = value

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

    if (
        raw_headers.get("connection") == "Upgrade"
        and raw_headers.get("upgrade") == "websocket"
    ):
        return await handle_client_ws(reader, writer, scope, raw_headers)

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


async def handle_client_ws(reader, writer, scope, raw_headers):
    scope["type"] = "websocket"
    connect_sent = False

    async def receive() -> dict:
        nonlocal connect_sent

        if not connect_sent:
            connect_sent = True
            return {"type": "websocket.connect"}

        # Read frame header
        header = await reader.read(2)

        unpacked = struct.unpack("<BB", header)
        fin = unpacked[0] & (1 << 7) > 0
        opcode = unpacked[0] & 0x0F
        mask = unpacked[1] & (1 << 7) > 0
        payload_len = unpacked[1] & 0x7F

        if payload_len == 126:
            l = await reader.read(2)
            u = struct.unpack("<H", l)
            payload_len = u[0]
        elif payload_len == 127:
            l = await reader.read(8)
            u = struct.unpack("<Q", l)
            payload_len = u[0]

        if mask:
            masking_key = await reader.read(4)

        payload = await reader.read(payload_len)

        if mask:
            unmasked = bytearray()
            for i in range(len(payload)):
                unmasked.append(payload[i] ^ masking_key[i % 4])
            payload = bytes(unmasked)

        event = {"type": "websocket.receive"}

        if opcode == 1:
            event["text"] = payload.decode()  # TODO encoding ??
        elif opcode == 2:
            event["bytes"] = payload
        elif opcode == 8:
            close_code = 1005  # Default
            if len(payload):
                u = struct.unpack(">H", payload)
                close_code = u[0]
            return {"type": "websocket.disconnect", "code": close_code}

        return event

    async def send(message):
        print(message)
        if message["type"] == "websocket.accept":
            key = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            i = raw_headers["Sec-WebSocket-Key".lower()]
            h = hashlib.sha1(f"{i}{key}".encode())
            accept = base64.b64encode(h.digest()).decode()

            # Complete HTTP handshake - Upgrade to websocket connection
            headers = [
                "HTTP/1.1 101 Switching Protocols",
                "Upgrade: websocket",
                "Connection: Upgrade",
                f"Sec-WebSocket-Accept: {accept}",
                "",
            ]

            writer.writelines([f"{line}\r\n".encode() for line in headers])
            await writer.drain()
        elif message["type"] == "websocket.send":
            payload = b""

            if "text" in message:
                payload = message["text"].encode()
                writer.write(bytes([(1 << 7) | 1]))  # opcode 1
            elif "bytes" in message:
                payload = message["bytes"]
                writer.write(bytes([(1 << 7) | 2]))  # opcode 2

            # Send payload length
            if len(payload) <= 125:
                writer.write(bytes([len(payload)]))
            elif len(payload) < 0xFFFF:
                l = len(payload).to_bytes(2, "big")
                writer.write(bytes([126]) + l)
            else:
                l = len(payload).to_bytes(8, "big")
                writer.write(bytes([127]) + l)

            writer.write(payload)
            await writer.drain()
        elif message["type"] == "websocket.close":
            code = message.get("code", 1000)
            writer.write(bytes([1 << 7 | 8]))  # opcode 8
            writer.write(bytes([2]) + code.to_bytes(2, "big"))
            await writer.drain()
            writer.close()
            await writer.wait_closed()

    await app(scope, receive, send)


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8000)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    print("Listening on http://127.0.0.1:8000")
    asyncio.run(main())
