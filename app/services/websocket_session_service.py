import asyncio
import base64
import contextlib
import os
import threading
import traceback

from app.agent_backends import create_agent_backend
from app.protocol import parse_client_message
from starlette.websockets import WebSocketDisconnect
from .websocket_service import (
    send_v2_ack,
    send_v2_websocket_event,
    send_websocket_message,
)


EXCLUDE_STREAM_TYPES = [
    "language",
    "active_line",
    "end_of_execution",
    "start_of_message",
    "end_of_message",
    "start_of_code",
    "end_of_code",
]

CLIENT_LIFECYCLE_EVENTS = {
    "character.message.received",
    "character.message.rendered",
    "character.speech.start",
    "character.speech.done",
    "character.speech.error",
    "character.response.done",
}


async def _stream_agent_chunks(agent_backend, message, cancel_event):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def enqueue(item):
        asyncio.run_coroutine_threadsafe(queue.put(item), loop).result()

    def worker():
        try:
            for chunk in agent_backend.stream(message):
                if cancel_event.is_set():
                    break
                enqueue(("chunk", chunk))
        except Exception as exc:
            enqueue(("error", exc))
        finally:
            enqueue(("done", None))

    threading.Thread(target=worker, daemon=True).start()

    while True:
        item_type, value = await queue.get()
        if item_type == "done":
            break
        if item_type == "error":
            raise value
        yield value


async def stream_websocket_session(websocket, connection_manager=None):
    language = os.getenv("LANGUAGE") or "japanese"

    try:
        agent_backend = create_agent_backend(language)
        agent_backend.prepare()

        saved_file = ""
        client_protocol_version = "1"
        active_task = None
        active_cancel_event = None
        send_lock = asyncio.Lock()

        async def send_message(
            message,
            role,
            message_type="",
            emotion="neutral",
            protocol_version=None,
        ):
            async with send_lock:
                await send_websocket_message(
                    websocket,
                    message,
                    role,
                    message_type,
                    emotion,
                    protocol_version or client_protocol_version,
                )

        async def send_v2_event(
            event_type,
            payload=None,
            session_id=None,
            request_id=None,
            metadata=None,
        ):
            async with send_lock:
                await send_v2_websocket_event(
                    websocket,
                    event_type,
                    payload,
                    session_id=session_id,
                    request_id=request_id,
                    metadata=metadata,
                )

        async def send_ack(event, status="ok", message=""):
            async with send_lock:
                await send_v2_ack(websocket, event, status=status, message=message)

        async def process_chat_event(event, message_content, protocol_version, cancel_event):
            nonlocal saved_file

            if saved_file != "":
                message_content = saved_file + message_content
                saved_file = ""

            await send_message("", "assistant", "start", protocol_version=protocol_version)

            message = ""
            prev_type = ""
            is_source_code = False
            was_cancelled = False

            try:
                async for chunk in _stream_agent_chunks(
                    agent_backend, message_content, cancel_event
                ):
                    if cancel_event.is_set():
                        was_cancelled = True
                        break

                    current_type = chunk["type"]
                    if current_type in EXCLUDE_STREAM_TYPES:
                        prev_type = current_type
                        continue

                    should_flush = message and (
                        current_type != prev_type
                        or (
                            len(message) > 15
                            and (
                                message[-1]
                                in ["、", "。", "！", "？", "；", "…", "："]
                                or message[-1] == "\n"
                            )
                        )
                    )
                    if should_flush:
                        if "```" in message:
                            is_source_code = not is_source_code
                        else:
                            type_ = "code" if is_source_code else prev_type
                            await send_message(
                                message, type_, protocol_version=protocol_version
                            )
                        message = ""

                    if current_type == "executing":
                        message += (
                            f"{chunk['content']}\n\n========================\n"
                            "running...\n========================"
                        )
                    else:
                        content = chunk.get("content")
                        if isinstance(content, dict):
                            await send_message(
                                content.get("content", ""),
                                "code" if is_source_code else current_type,
                                protocol_version=protocol_version,
                            )
                        elif isinstance(content, str):
                            message += content

                    prev_type = current_type
            except asyncio.CancelledError:
                was_cancelled = True
                cancel_event.set()
                agent_backend.cancel()
            finally:
                if message and not was_cancelled:
                    await send_message(
                        message,
                        "code" if is_source_code else prev_type,
                        protocol_version=protocol_version,
                    )

                if was_cancelled and protocol_version == "2":
                    await send_v2_event(
                        "chat.done",
                        {
                            "text": "",
                            "role": "assistant",
                            "emotion": "neutral",
                            "cancelled": True,
                        },
                        session_id=event.sessionId,
                        request_id=event.id,
                    )
                else:
                    await send_message(
                        "",
                        "assistant",
                        "end",
                        protocol_version=protocol_version,
                    )

        while True:
            try:
                print("Waiting for user message...")
                user_message = await websocket.receive_text()
                print(f"Received user message: {user_message}")

                event = parse_client_message(user_message)
                client_protocol_version = event.metadata.get(
                    "sourceProtocol", event.version
                )
                if connection_manager:
                    connection_manager.set_protocol_version(
                        websocket, client_protocol_version
                    )

                if event.version == "2" and client_protocol_version == "2":
                    await send_ack(event)

                parsed_data = event.payload
                message_content = parsed_data.get("text") or parsed_data.get("content")
                message_type = event.type

                if message_type == "session.hello":
                    await send_v2_event(
                        "session.ready",
                        {
                            "protocolVersion": "2",
                            "capabilities": [
                                "ack",
                                "ping",
                                "pong",
                                "chat.message",
                                "chat.start",
                                "chat.delta",
                                "chat.done",
                                "chat.error",
                                "file.upload",
                                "control.cancel",
                                "character.message.received",
                                "character.message.rendered",
                                "character.speech.start",
                                "character.speech.done",
                                "character.speech.error",
                                "character.response.done",
                            ],
                        },
                        session_id=event.sessionId,
                        request_id=event.id,
                    )
                    continue

                if message_type in CLIENT_LIFECYCLE_EVENTS:
                    print(
                        "Received client lifecycle event: "
                        f"{message_type} requestId={event.requestId or parsed_data.get('requestId')}"
                    )
                    continue

                if message_type == "ping":
                    await send_v2_event(
                        "pong",
                        {"requestId": event.id},
                        session_id=event.sessionId,
                        request_id=event.id,
                    )
                    continue

                if message_type == "control.cancel":
                    if active_task and not active_task.done() and active_cancel_event:
                        active_cancel_event.set()
                        agent_backend.cancel()
                        active_task.cancel()
                    else:
                        await send_v2_event(
                            "chat.done",
                            {
                                "text": "",
                                "role": "assistant",
                                "emotion": "neutral",
                                "cancelled": True,
                            },
                            session_id=event.sessionId,
                            request_id=event.requestId or event.id,
                        )
                    continue

                if message_type == "chat.message" and message_content != "":
                    if active_task and not active_task.done():
                        if client_protocol_version == "2":
                            await send_v2_event(
                                "chat.error",
                                {"message": "Another request is already running."},
                                session_id=event.sessionId,
                                request_id=event.id,
                            )
                        else:
                            await send_message(
                                "別の処理が実行中です。",
                                "assistant",
                                protocol_version=client_protocol_version,
                            )
                        continue

                    active_cancel_event = threading.Event()
                    active_task = asyncio.create_task(
                        process_chat_event(
                            event,
                            message_content,
                            client_protocol_version,
                            active_cancel_event,
                        )
                    )
                    continue

                if message_type == "file.upload":
                    file_name = parsed_data.get("fileName")
                    base64_data = parsed_data.get("fileData").split(",")[1]
                    file_data = base64.b64decode(base64_data)

                    directory = "./workspace"
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    file_path = os.path.join(directory, file_name)
                    with open(file_path, "wb") as f:
                        f.write(file_data)

                    saved_file = (
                        f"{directory}/{file_name}にファイルを保存しました。"
                        if language == "japanese"
                        else f"Saved file to {directory}/{file_name}."
                    )
                    save_message = (
                        "ファイルを保存しました。"
                        if language == "japanese"
                        else "Saved file."
                    )
                    await send_message(
                        "",
                        "assistant",
                        "start",
                        protocol_version=client_protocol_version,
                    )
                    await send_message(
                        save_message,
                        "assistant",
                        protocol_version=client_protocol_version,
                    )
                    await send_message(
                        "",
                        "assistant",
                        "end",
                        protocol_version=client_protocol_version,
                    )
                    continue

                await send_message(
                    "",
                    "assistant",
                    "start",
                    protocol_version=client_protocol_version,
                )
                error_message = (
                    "不正な送信が送られたようです。"
                    if language == "japanese"
                    else "An invalid message was sent."
                )
                await send_message(
                    error_message,
                    "assistant",
                    protocol_version=client_protocol_version,
                )
                await send_message(
                    "",
                    "assistant",
                    "end",
                    protocol_version=client_protocol_version,
                )

            except WebSocketDisconnect:
                raise
            except Exception as e:
                print(f"Error in message processing: {e}")
                traceback.print_exc()
                await send_message(
                    "エラーが発生しました。",
                    "assistant",
                    protocol_version=client_protocol_version,
                )

    except WebSocketDisconnect:
        raise
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
    finally:
        with contextlib.suppress(RuntimeError):
            await websocket.close()
