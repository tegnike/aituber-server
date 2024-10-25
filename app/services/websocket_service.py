import json
import asyncio


async def send_websocket_message(websocket, message, role, type="", emotion="neutral"):
    role = "assistant" if role == "message" else role

    if not websocket:
        print("Can't send message, WebSocket connection is closed.")
        return
    elif type == "" and message == "":
        print("Can't send message, message is empty.")
        return
    else:
        json_data = json.dumps(
            {"role": role, "text": message, "emotion": emotion, "type": type},
            ensure_ascii=False,
        )
        print(f"Sending message: {json_data}")
        await websocket.send_text(json_data)
        await asyncio.sleep(0.01)  # 10ミリ秒の遅延を追加
        print("Send complete.")
