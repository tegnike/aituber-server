import json


async def send_websocket_message(websocket, message, type):
    # type別にrole変数に値を設定
    role = "assistant" if type == "message" else type

    if websocket and message != "":
        json_data = json.dumps({"role": role, "text": message}, ensure_ascii=False)
        print(f"Sending message: {json_data}")
        await websocket.send_text(json_data)
        print("Send cmplete.")
    else:
        print("Can't send message, WebSocket connection is closed.")
