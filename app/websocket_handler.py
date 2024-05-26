import ast
import asyncio

import websockets

import rechat

api_endpoint: str = rechat.api_endpoint
console = rechat.console

websocket: websockets.WebSocketClientProtocol | None = None


async def connect():
    global websocket, api_endpoint
    # Replace https or http to ws
    if api_endpoint.startswith("http://"):
        api_endpoint = api_endpoint.replace("http://", "ws://")
    elif api_endpoint.startswith("https://"):
        api_endpoint = api_endpoint.replace("https://", "wss://")
    url = api_endpoint + 'chat'

    websocket = await websockets.connect(url)


async def disconnect() -> None:
    global websocket
    if websocket is not None:
        await websocket.close()
        websocket = None


async def send_message(message: str) -> None:
    global websocket

    if message == '':
        return

    if websocket is not None:
        await websocket.send(message)


async def receive_message(messages: list[str], chat_close_signal) -> None:
    global websocket
    if websocket is not None:
        try:
            message = await asyncio.wait_for(websocket.recv(), timeout=1)
            message = ast.literal_eval(message)
            messages.append(message)
        except asyncio.TimeoutError:
            if chat_close_signal.is_set():
                return


async def main(uuid: str, partner_uuid: str, access_token: str, messages: list[str], chat_close_signal) \
        -> None:
    await connect()

    # Send credentials to the server (FORMAT IS 'TOKEN|UUID|PARTNER_UUID')
    credentials = f'{access_token}|{uuid}|{partner_uuid}'
    await send_message(credentials)

    # Receive initial messages
    try:
        history_str = await websocket.recv()
        history: list = ast.literal_eval(history_str)
        messages.extend(reversed(history))
    except websockets.exceptions.ConnectionClosedError:
        console.print('Connection closed unexpectedly. most likely connection issue with the API server\n'
                      'Basically you can\'t chat and have to try using your own API (Localhost)'
                      '.\n\n\n\n\n\n\n\n\n\n.',
                      justify='center', style='bold red')
        await disconnect()

    while not chat_close_signal.is_set():
        await receive_message(messages, chat_close_signal)

    await disconnect()


def websocket_run(uuid: str, partner_uuid: str, access_token: str, messages: list[str], chat_close_signal) \
        -> None:
    asyncio.run(main(uuid, partner_uuid, access_token, messages, chat_close_signal))
