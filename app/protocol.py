import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class WebSocketEnvelope(BaseModel):
    version: str = "2"
    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex}")
    type: str
    sessionId: str = Field(default_factory=lambda: f"session_{uuid4().hex}")
    timestamp: str = Field(default_factory=_now_iso)
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    requestId: Optional[str] = None


def create_event(
    event_type: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> WebSocketEnvelope:
    data: Dict[str, Any] = {
        "type": event_type,
        "payload": payload or {},
        "metadata": metadata or {},
    }
    if session_id:
        data["sessionId"] = session_id
    if request_id:
        data["requestId"] = request_id
    return WebSocketEnvelope(**data)


def create_ack_event(
    event: WebSocketEnvelope,
    *,
    status: str = "ok",
    message: str = "",
) -> WebSocketEnvelope:
    return create_event(
        "ack",
        {
            "requestId": event.id,
            "type": event.type,
            "status": status,
            **({"message": message} if message else {}),
        },
        session_id=event.sessionId,
        request_id=event.id,
    )


def create_server_message_event(message: str, role: str = "message") -> WebSocketEnvelope:
    return create_event(
        "server.message",
        {
            "text": message,
            "role": role,
        },
        metadata={"source": "http"},
    )


def parse_client_message(raw_message: str) -> WebSocketEnvelope:
    data = json.loads(raw_message)
    if data.get("version") == "2":
        return WebSocketEnvelope.model_validate(data)
    return legacy_to_v2(data)


def legacy_to_v2(data: Dict[str, Any]) -> WebSocketEnvelope:
    legacy_type = data.get("type", "")

    if legacy_type == "chat":
        payload: Dict[str, Any] = {"text": data.get("content", "")}
        if data.get("image"):
            payload["image"] = data["image"]
        return create_event(
            "chat.message",
            payload,
            metadata={"legacyType": legacy_type, "sourceProtocol": "1"},
        )

    if legacy_type == "file":
        return create_event(
            "file.upload",
            {
                "fileName": data.get("fileName", ""),
                "fileData": data.get("fileData", ""),
            },
            metadata={"legacyType": legacy_type, "sourceProtocol": "1"},
        )

    return create_event(
        "legacy.unknown",
        data,
        metadata={"legacyType": legacy_type, "sourceProtocol": "1"},
    )


def legacy_response_to_v2(
    message: str,
    role: str,
    message_type: str = "",
    emotion: str = "neutral",
) -> WebSocketEnvelope:
    if message_type == "start":
        event_type = "chat.start"
    elif message_type == "end":
        event_type = "chat.done"
    else:
        event_type = "chat.delta"

    return create_event(
        event_type,
        {
            "text": message,
            "role": "assistant" if role == "message" else role,
            "emotion": emotion,
            "legacyType": message_type,
        },
    )
