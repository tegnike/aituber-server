import json
import base64

async def send_websocket_message(websocket, message, type):
    # type別にrole変数に値を設定
    role = "assistant" if type == "message" else type

    if websocket and message != "":
        json_data = json.dumps({"role": role, "text": message}, ensure_ascii=False)
        print(f"Sending message: {json_data}")
        await websocket.send({"type": "websocket.send", "text": json_data})
        print(f"Send cmplete.")
    else:
        print("Can't send message, WebSocket connection is closed.")

async def send_websocket_file(websocket, file_name):
    if websocket and file_name != "":
        # ファイルをバイナリモードで読み込み
        with open(file_name, 'rb') as file:
            file_data = file.read()

        # ファイルデータをBase64エンコードして文字列に変換
        encoded_file_data = base64.b64encode(file_data).decode('utf-8')
        json_data = json.dumps({"role": "file", "file_name": file_name, "content": encoded_file_data}, ensure_ascii=False)
        print(f"Sending message: {json_data}")

        # JSONデータを文字列にシリアライズして送信
        await websocket.send(json.dumps(json_data))
        print(f"Send cmplete.")
    else:
        print("Can't send message, WebSocket connection is closed.")
