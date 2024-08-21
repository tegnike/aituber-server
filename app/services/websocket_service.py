import json
import asyncio


async def send_websocket_message(websocket, message, type, state=""):
    # type別にrole変数に値を設定
    role = "assistant" if type == "message" else type

    if not websocket:
        print("Can't send message, WebSocket connection is closed.")
        return
    elif state == "" and message == "":
        print("Can't send message, message is empty.")
        return
    else:
        json_data = json.dumps(
            {"role": role, "text": message, "state": state}, ensure_ascii=False
        )
        print(f"Sending message: {json_data}")
        await websocket.send_text(json_data)
        await asyncio.sleep(0.01)  # 10ミリ秒の遅延を追加
        print("Send complete.")
