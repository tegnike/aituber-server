from fastapi import APIRouter, WebSocket
from ..services.open_interpreter_service import stream_open_interpreter
import asyncio
from datetime import datetime

router = APIRouter()
waiting_start_time = asyncio.Queue()

async def main(websocket, waiting_start_time):
    task1 = asyncio.create_task(stream_open_interpreter(websocket, waiting_start_time))
    await asyncio.gather(task1)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await waiting_start_time.put(datetime.utcnow())
    try:
        await main(websocket, waiting_start_time)
    except Exception as e:
        print(f"WebSocket Endpoint Error: {e}")
        await websocket.close()

@router.get("/test")
async def test():
    print("/test called.")
