import os
import json
import base64
import traceback
from interpreter import interpreter
from datetime import datetime
from .websocket_service import send_websocket_message

async def stream_open_interpreter(websocket):
    language = os.getenv('LANGUAGE') or "japanese"

    try:
        # 1日の記憶を保持する
        interpreter.conversation_filename = f"{datetime.now().strftime('%Y%m%d')}.json"
        interpreter.conversation_history_path = "./conversation_histories/"
        if os.path.exists(interpreter.conversation_history_path + interpreter.conversation_filename):
            # あったら読み込んで記憶として設定する
            with open(interpreter.conversation_history_path + interpreter.conversation_filename, "r") as f:
                interpreter.messages = json.load(f)
            print("Loaded conversation history.")
        else:
            # なかったら作成する
            with open(interpreter.conversation_history_path + interpreter.conversation_filename, "w") as f:
                json.dump([], f)
            print("Created conversation history.")

        interpreter.model = "gpt-4o"
        interpreter.auto_run = True
        # interpreter.debug_mode = True
        interpreter.system_message = f"""
You can use the following libraries without installing:
- pandas
- numpy
- matplotlib
- seaborn
- scikit-learn
- pandas-datareader
- mplfinance
- yfinance
- requests
- scrapy
- beautifulsoup4
- opencv-python
- ffmpeg-python
- PyMuPDF
- pytube
- pyocr
- easyocr
- pydub
- pdfkit
- weasyprint
Your workspace is `./workspace` folder. If you make an output file, please put it in `./workspace/output`.
{'[[Please answer in Japanese. 日本語でお答えください。]]' if language == 'japanese' else ''}
        """

        message = ""
        saved_file = ""
        prev_type = ""

        while True:
            if message != "" and message != "\n":
                await send_websocket_message(websocket, message, prev_type)

            message = ""
            prev_type = ""

            # WebSocketでメッセージ受け取り待機
            print("Waiting for user message...")
            user_message = await websocket.receive_text()
            print(f"Received user message: {user_message}")

            parsed_data = json.loads(user_message)
            message_content = parsed_data.get("content")
            message_type = parsed_data.get("type")

            # WebSocketでテキストメッセージを受け取った場合
            # ex. {"type": "message", "text": "こんにちは"}
            if message_type == "chat" and message_content != "":
                if saved_file != "":
                    user_message = saved_file + user_message
                    saved_file = ""

                # OpenInterpreterの結果をstreamモードで取得、chunk毎に処理
                is_source_code = False
                for chunk in interpreter.chat(message_content, display=True, stream=True):
                    current_type = chunk["type"]
                    exculde_types = ["language", "active_line", "end_of_execution", "start_of_message", "end_of_message", "start_of_code", "end_of_code"]
                    if current_type not in exculde_types:
                        # message typeの場合は、文節に区切ってメッセージを送信
                        if message and (current_type != prev_type or (len(message) > 15 and message[-1] in ['、', '。', '！', '？', '；', '…', '：'] or message[-1] == "\n")):
                            if message != "":
                                if "```" in message:
                                    # Toggle is_source_code
                                    is_source_code = not is_source_code
                                else:
                                    type_ = "code" if is_source_code else prev_type
                                    await send_websocket_message(websocket, message, type_)
                            message = ""

                        if current_type == "executing":
                            message += f"{chunk['content']}\n\n========================\nrunning...\n========================"
                        else:
                            try:
                                if isinstance(chunk["content"], dict):
                                    await send_websocket_message(websocket, chunk["content"]["content"], type_)
                                elif isinstance(chunk["content"], str):
                                    message += chunk["content"]
                                else:
                                    pass
                            except KeyError:
                                pass
                        prev_type = current_type

            # WebSocketでファイルを受け取った場合
            # ex. {"type": "file", "fileName": "sample.txt", "fileData": "data:;base64,SGVsbG8sIHdvcmxkIQ=="}
            elif message_type == "file":
                # JSONデータをパースして、ファイル名とファイルデータを取得
                file_name = parsed_data.get("fileName")
                base64_data = parsed_data.get("fileData").split(",")[1]
                file_data = base64.b64decode(base64_data)

                # ファイルを保存するディレクトリを指定
                directory = "./workspace"

                # ディレクトリが存在しない場合、作成
                if not os.path.exists(directory):
                    os.makedirs(directory)

                # ファイルのフルパスを作成
                file_path = os.path.join(directory, file_name)

                # ファイルを保存
                with open(file_path, "wb") as f:
                    f.write(file_data)

                # メッセージを追加
                saved_file = f"{directory}/{file_name}にファイルを保存しました。" if language == 'japanese' else f"Saved file to {directory}/{file_name}."
                save_message = "ファイルを保存しました。" if language == 'japanese' else f"Saved file."
                await send_websocket_message(websocket, save_message, "assistant")

            # WebSocketで未設定のメッセージを受け取った場合
            else:
                error_message = "不正な送信が送られたようです。" if language == 'japanese' else "An invalid message was sent."
                await send_websocket_message(websocket, error_message, "assistant")

    except Exception as e:
        print("Errors:", e)
        traceback.print_exc()

        await websocket.close()
