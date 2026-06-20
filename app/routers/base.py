from fastapi import APIRouter, WebSocket, Request, WebSocketDisconnect
from app.connection_manager import ConnectionManager
from app.protocol import create_server_message_event
from ..services.websocket_session_service import stream_websocket_session

router = APIRouter()


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await stream_websocket_session(websocket, manager)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/send_message")
async def send_message(request: Request):
    message = await request.json()
    event = create_server_message_event(message["message"], message.get("type", "message"))
    await manager.send_event_to_all(event)
    return {"status": "ok", "message": message["message"], "eventId": event.id}


@router.get("/")
async def test():
    print("/test called.")
    return {"message": "Hello World"}
