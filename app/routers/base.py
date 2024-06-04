from typing import List
from fastapi import APIRouter, WebSocket, Request, WebSocketDisconnect
from ..services.open_interpreter_service import stream_open_interpreter
from ..services.websocket_service import send_websocket_message

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_message_to_all(self, message: str, type: str):
        for websocket in self.active_connections:
            await send_websocket_message(websocket, message, type)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await stream_open_interpreter(websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/send_message")
async def send_message(request: Request):
    message = await request.json()
    await manager.send_message_to_all(message["message"], message.get("type", "message"))
    return {"status": "ok", "message": message["message"]}


@router.get("/")
async def test():
    print("/test called.")
    return {"message": "Hello World"}
