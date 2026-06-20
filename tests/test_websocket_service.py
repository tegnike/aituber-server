import asyncio
import json

from app.protocol import parse_client_message
from app.protocol import create_server_message_event
from app.services.websocket_service import (
    send_server_message_event,
    send_v2_ack,
    send_v2_websocket_event,
    send_websocket_message,
)


class DummyWebSocket:
    def __init__(self):
        self.sent = []

    async def send_text(self, message):
        self.sent.append(message)


def test_send_websocket_message_keeps_legacy_shape_by_default():
    websocket = DummyWebSocket()

    asyncio.run(send_websocket_message(websocket, "hello", "assistant"))

    assert json.loads(websocket.sent[0]) == {
        "role": "assistant",
        "text": "hello",
        "emotion": "neutral",
        "type": "",
    }


def test_send_websocket_message_can_emit_v2_events():
    websocket = DummyWebSocket()

    asyncio.run(
        send_websocket_message(
            websocket,
            "hello",
            "assistant",
            emotion="happy",
            protocol_version="2",
        )
    )

    sent = json.loads(websocket.sent[0])
    assert sent["version"] == "2"
    assert sent["type"] == "chat.delta"
    assert sent["payload"]["text"] == "hello"
    assert sent["payload"]["role"] == "assistant"
    assert sent["payload"]["emotion"] == "happy"


def test_send_v2_websocket_event_sends_envelope():
    websocket = DummyWebSocket()

    asyncio.run(
        send_v2_websocket_event(
            websocket,
            "pong",
            {"requestId": "msg_ping"},
            session_id="session_test",
            request_id="msg_ping",
        )
    )

    sent = json.loads(websocket.sent[0])
    assert sent["version"] == "2"
    assert sent["type"] == "pong"
    assert sent["sessionId"] == "session_test"
    assert sent["requestId"] == "msg_ping"
    assert sent["payload"]["requestId"] == "msg_ping"


def test_send_v2_ack_sends_request_ack():
    websocket = DummyWebSocket()
    event = parse_client_message(
        json.dumps(
            {
                "version": "2",
                "id": "msg_request",
                "type": "chat.message",
                "sessionId": "session_test",
                "timestamp": "2026-06-20T00:00:00.000Z",
                "payload": {"text": "hello"},
            }
        )
    )

    asyncio.run(send_v2_ack(websocket, event))

    sent = json.loads(websocket.sent[0])
    assert sent["type"] == "ack"
    assert sent["requestId"] == "msg_request"
    assert sent["payload"]["status"] == "ok"


def test_send_server_message_event_emits_v2_chat_sequence():
    websocket = DummyWebSocket()
    event = create_server_message_event("hello", "message")

    asyncio.run(send_server_message_event(websocket, event, protocol_version="2"))

    sent = [json.loads(message) for message in websocket.sent]
    assert [message["type"] for message in sent] == [
        "chat.start",
        "chat.delta",
        "chat.done",
    ]
    assert all(message["requestId"] == event.id for message in sent)
    assert sent[1]["payload"]["text"] == "hello"


def test_send_server_message_event_keeps_legacy_chat_sequence():
    websocket = DummyWebSocket()
    event = create_server_message_event("hello", "message")

    asyncio.run(send_server_message_event(websocket, event))

    sent = [json.loads(message) for message in websocket.sent]
    assert [message["type"] for message in sent] == ["start", "", "end"]
    assert sent[1]["text"] == "hello"
