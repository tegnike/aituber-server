import asyncio
import json

from app.connection_manager import ConnectionManager
from app.protocol import create_server_message_event


class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message):
        self.sent.append(message)


def test_connection_manager_accepts_and_sends_session_ready():
    manager = ConnectionManager()
    websocket = DummyWebSocket()

    asyncio.run(manager.connect(websocket))

    assert websocket.accepted is True
    assert websocket in manager.active_connections
    sent = json.loads(websocket.sent[0])
    assert sent["version"] == "2"
    assert sent["type"] == "session.ready"
    assert "control.cancel" in sent["payload"]["capabilities"]
    assert "character.response.done" in sent["payload"]["capabilities"]


def test_connection_manager_tracks_protocol_versions():
    manager = ConnectionManager()
    websocket = DummyWebSocket()
    asyncio.run(manager.connect(websocket))

    assert manager.get_protocol_version(websocket) == "1"

    manager.set_protocol_version(websocket, "2")

    assert manager.get_protocol_version(websocket) == "2"

    manager.disconnect(websocket)

    assert websocket not in manager.active_connections
    assert manager.get_protocol_version(websocket) == "1"


def test_connection_manager_sends_server_message_event_as_v2_for_v2_clients():
    manager = ConnectionManager()
    websocket = DummyWebSocket()
    asyncio.run(manager.connect(websocket))
    manager.set_protocol_version(websocket, "2")

    event = create_server_message_event("hello", "message")
    asyncio.run(manager.send_event_to_all(event))

    sent = [json.loads(message) for message in websocket.sent[1:]]
    assert [message["type"] for message in sent] == [
        "chat.start",
        "chat.delta",
        "chat.done",
    ]
    assert sent[1]["payload"]["text"] == "hello"
