import asyncio


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    request = await reader.readuntil(b"\r\n\r\n")

    print(request.decode())

    writer.writelines((b"HTTP/1.1 200 OK\r\n", b"\r\n"))
    await writer.drain()
    writer.write(
        b"""
        <html>
            <head>
                <title>An Example Page</title>
            </head>
            <body>
                <p>Hello World, this is a very simple HTML document.</p>
            </body>
        </html>
        """
    )
    await writer.drain()
    writer.write(b"\r\n")
    await writer.drain()

    writer.close()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 8000)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
