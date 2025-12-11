import ast
import asyncio
import websockets
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzY1NDMxNDM3fQ.xVh1YhDlUYzTO2sM7c9dyi3QvLmvafg8fzTqzHXCpTQ"
endpoint = f"ws://127.0.0.1:8001/ws/process_urls?token={token}"


async def process_url(path):
    async with websockets.connect(endpoint) as ws:

        hello = await ws.recv()
        print("Server:", hello)

        urls = []
        print(urls)
        with open(path, 'r', encoding="utf-8") as lines:
            for line in lines:
                row = ast.literal_eval(line)
                urls.append(row["URL"])

        payload = {"urls": urls}

        print("Sending URLs...")
        await ws.send(json.dumps(payload))

        while True:
            try:
                msg = await ws.recv()
                print("Server:", msg)
            except websockets.ConnectionClosed:
                print("Connection closed by server")
                break
        
        await ws.close()

if __name__ == "__main__":
    asyncio.run(process_url("items_Kavos_parse_bol_905.jl"))