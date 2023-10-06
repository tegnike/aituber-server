from fastapi import APIRouter, WebSocket
from ..services.open_interpreter_service import stream_open_interpreter
import asyncio

router = APIRouter()

async def main(websocket):
    task1 = asyncio.create_task(stream_open_interpreter(websocket))
    await asyncio.gather(task1)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await main(websocket)
    except Exception as e:
        print(f"WebSocket Endpoint Error: {e}")
        await websocket.close()

@router.get("/test")
async def test():
    print("/test called.")
