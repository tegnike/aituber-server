import json
import asyncio

from app.protocol import create_ack_event, legacy_response_to_v2


async def send_websocket_message(
    websocket, message, role, type="", emotion="neutral", protocol_version="1"
):
    role = "assistant" if role == "message" else role

    if not websocket:
        print("Can't send message, WebSocket connection is closed.")
        return
    elif type == "" and message == "":
        print("Can't send message, message is empty.")
        return
    else:
        if protocol_version == "2":
            json_data = legacy_response_to_v2(
                message, role, type, emotion
            ).model_dump_json()
        else:
            json_data = json.dumps(
                {"role": role, "text": message, "emotion": emotion, "type": type},
                ensure_ascii=False,
            )
        print(f"Sending message: {json_data}")
        await websocket.send_text(json_data)
        await asyncio.sleep(0.01)  # 10ミリ秒の遅延を追加
        print("Send complete.")


async def send_v2_websocket_event(
    websocket, event_type, payload=None, session_id=None, request_id=None, metadata=None
):
    if not websocket:
        print("Can't send event, WebSocket connection is closed.")
        return

    from app.protocol import create_event

    event = create_event(
        event_type,
        payload or {},
        session_id=session_id,
        request_id=request_id,
        metadata=metadata or {},
    )
    json_data = event.model_dump_json()
    print(f"Sending v2 event: {json_data}")
    await websocket.send_text(json_data)
    await asyncio.sleep(0.01)
    print("Send complete.")


async def send_v2_ack(websocket, event, status="ok", message=""):
    if not websocket:
        print("Can't send ack, WebSocket connection is closed.")
        return

    ack = create_ack_event(event, status=status, message=message)
    json_data = ack.model_dump_json()
    print(f"Sending ack: {json_data}")
    await websocket.send_text(json_data)
    await asyncio.sleep(0.01)
    print("Send complete.")


async def send_server_message_event(websocket, event, protocol_version="1"):
    message = event.payload.get("text", "")
    role = event.payload.get("role", "message")

    if protocol_version == "2":
        await send_v2_websocket_event(
            websocket,
            "chat.start",
            {"text": "", "role": "assistant", "emotion": "neutral"},
            session_id=event.sessionId,
            request_id=event.id,
            metadata={"sourceEventType": event.type},
        )
        await send_v2_websocket_event(
            websocket,
            "chat.delta",
            {
                "text": message,
                "role": "assistant" if role == "message" else role,
                "emotion": "neutral",
            },
            session_id=event.sessionId,
            request_id=event.id,
            metadata={"sourceEventType": event.type},
        )
        await send_v2_websocket_event(
            websocket,
            "chat.done",
            {"text": "", "role": "assistant", "emotion": "neutral"},
            session_id=event.sessionId,
            request_id=event.id,
            metadata={"sourceEventType": event.type},
        )
        return

    await send_websocket_message(websocket, "", "assistant", "start")
    await send_websocket_message(websocket, message, role)
    await send_websocket_message(websocket, "", "assistant", "end")
