import asyncio
import contextlib
import json
import time

from app.services import websocket_session_service


class QueueWebSocket:
    def __init__(self):
        self.incoming = asyncio.Queue()
        self.sent = []
        self.closed = False

    async def receive_text(self):
        return await self.incoming.get()

    async def send_text(self, message):
        self.sent.append(message)

    async def close(self):
        self.closed = True


class CancellableBackend:
    def __init__(self):
        self.cancel_called = False

    def prepare(self):
        return

    def stream(self, message):
        yield {"type": "message", "content": "処理中です。"}
        while not self.cancel_called:
            time.sleep(0.01)

    def cancel(self):
        self.cancel_called = True


def v2_event(event_type, payload=None, request_id=None):
    return json.dumps(
        {
            "version": "2",
            "id": f"msg_{event_type}",
            "type": event_type,
            "sessionId": "session_test",
            "timestamp": "2026-06-20T00:00:00.000Z",
            "payload": payload or {},
            **({"requestId": request_id} if request_id else {}),
        }
    )


def test_stream_websocket_session_can_cancel_active_stream(monkeypatch):
    async def run_test():
        backend = CancellableBackend()
        monkeypatch.setattr(
            websocket_session_service,
            "create_agent_backend",
            lambda language: backend,
        )
        websocket = QueueWebSocket()
        task = asyncio.create_task(
            websocket_session_service.stream_websocket_session(websocket)
        )

        await websocket.incoming.put(
            v2_event("chat.message", {"text": "長い処理を開始して"})
        )
        await asyncio.sleep(0.05)
        await websocket.incoming.put(v2_event("control.cancel", request_id="msg_chat"))

        for _ in range(50):
            sent = [json.loads(message) for message in websocket.sent]
            if any(
                message["type"] == "chat.done"
                and message["payload"].get("cancelled") is True
                for message in sent
            ):
                break
            await asyncio.sleep(0.02)

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        sent = [json.loads(message) for message in websocket.sent]
        assert backend.cancel_called is True
        assert any(
            message["type"] == "chat.done"
            and message["payload"].get("cancelled") is True
            for message in sent
        )

    asyncio.run(run_test())


def test_stream_websocket_session_accepts_client_lifecycle_events(monkeypatch):
    async def run_test():
        backend = CancellableBackend()
        monkeypatch.setattr(
            websocket_session_service,
            "create_agent_backend",
            lambda language: backend,
        )
        websocket = QueueWebSocket()
        task = asyncio.create_task(
            websocket_session_service.stream_websocket_session(websocket)
        )

        await websocket.incoming.put(
            v2_event(
                "character.response.done",
                {
                    "requestId": "msg_chat",
                    "speechSegmentCount": 1,
                },
                request_id="msg_chat",
            )
        )

        for _ in range(50):
            sent = [json.loads(message) for message in websocket.sent]
            if any(message["type"] == "ack" for message in sent):
                break
            await asyncio.sleep(0.02)

        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        sent = [json.loads(message) for message in websocket.sent]
        assert any(message["type"] == "ack" for message in sent)
        assert not any(message["type"] == "chat.delta" for message in sent)

    asyncio.run(run_test())
