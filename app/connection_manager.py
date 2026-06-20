from typing import TYPE_CHECKING, Dict, List

if TYPE_CHECKING:
    from fastapi import WebSocket
else:
    WebSocket = object

from app.protocol import WebSocketEnvelope, create_server_message_event
from app.services.websocket_service import send_server_message_event, send_v2_websocket_event


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.protocol_versions: Dict[int, str] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.protocol_versions[id(websocket)] = "1"
        await send_v2_websocket_event(
            websocket,
            "session.ready",
            {
                "protocolVersion": "2",
                "capabilities": [
                    "ack",
                    "ping",
                    "pong",
                    "chat.message",
                    "chat.start",
                    "chat.delta",
                    "chat.done",
                    "chat.error",
                    "file.upload",
                    "control.cancel",
                    "character.message.received",
                    "character.message.rendered",
                    "character.speech.start",
                    "character.speech.done",
                    "character.speech.error",
                    "character.response.done",
                ],
            },
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.protocol_versions.pop(id(websocket), None)

    def set_protocol_version(self, websocket: WebSocket, protocol_version: str):
        self.protocol_versions[id(websocket)] = protocol_version

    def get_protocol_version(self, websocket: WebSocket) -> str:
        return self.protocol_versions.get(id(websocket), "1")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_event_to_all(self, event: WebSocketEnvelope):
        closed_connections = []
        for websocket in self.active_connections:
            try:
                protocol_version = self.get_protocol_version(websocket)
                if event.type == "server.message":
                    await send_server_message_event(websocket, event, protocol_version)
            except RuntimeError:
                closed_connections.append(websocket)

        for closed_websocket in closed_connections:
            self.disconnect(closed_websocket)

    async def send_message_to_all(self, message: str, type: str):
        await self.send_event_to_all(create_server_message_event(message, type))
