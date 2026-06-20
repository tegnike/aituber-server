import json

from app.protocol import (
    create_ack_event,
    create_server_message_event,
    legacy_response_to_v2,
    parse_client_message,
)


def test_parse_legacy_chat_message_as_v2_envelope():
    event = parse_client_message(
        json.dumps(
            {
                "type": "chat",
                "content": "こんにちは",
                "image": "data:image/png;base64,abc",
            }
        )
    )

    assert event.version == "2"
    assert event.type == "chat.message"
    assert event.payload["text"] == "こんにちは"
    assert event.payload["image"] == "data:image/png;base64,abc"
    assert event.metadata["legacyType"] == "chat"
    assert event.metadata["sourceProtocol"] == "1"


def test_parse_v2_message_keeps_envelope_fields():
    event = parse_client_message(
        json.dumps(
            {
                "version": "2",
                "id": "msg_test",
                "type": "chat.message",
                "sessionId": "session_test",
                "timestamp": "2026-06-20T00:00:00.000Z",
                "payload": {"text": "hello"},
            }
        )
    )

    assert event.id == "msg_test"
    assert event.type == "chat.message"
    assert event.sessionId == "session_test"
    assert event.payload["text"] == "hello"


def test_legacy_response_start_maps_to_v2_chat_start():
    event = legacy_response_to_v2("", "assistant", "start")

    assert event.type == "chat.start"
    assert event.payload["role"] == "assistant"
    assert event.payload["legacyType"] == "start"


def test_legacy_response_message_maps_to_v2_chat_delta():
    event = legacy_response_to_v2("hello", "message", "", "happy")

    assert event.type == "chat.delta"
    assert event.payload["text"] == "hello"
    assert event.payload["role"] == "assistant"
    assert event.payload["emotion"] == "happy"


def test_create_ack_event_links_to_request():
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

    ack = create_ack_event(event)

    assert ack.type == "ack"
    assert ack.requestId == "msg_request"
    assert ack.payload["requestId"] == "msg_request"
    assert ack.payload["type"] == "chat.message"
    assert ack.payload["status"] == "ok"


def test_create_server_message_event_marks_http_source():
    event = create_server_message_event("hello", "message")

    assert event.type == "server.message"
    assert event.payload["text"] == "hello"
    assert event.payload["role"] == "message"
    assert event.metadata["source"] == "http"
