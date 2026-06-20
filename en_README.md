# AITuberKit Server Side

[Japanese version](./README.md)

## Overview

This is the dedicated WebSocket server for AITuberKit External Linkage Mode.

AITuberKit handles chat display, speech synthesis, character rendering, expressions, and motion control. This server acts as the WebSocket protocol server that connects AITuberKit to external processing.

It keeps the legacy JSON format as `legacy (v1 compatible)` while supporting the current `v2` WebSocket protocol, `ack`, heartbeat, cancel, and server initiated messages. There is no separate new `v1` protocol; legacy means the original JSON compatibility mode.

Open Interpreter has been removed. Response generation is separated behind the `AgentBackend` interface, and the current built-in backends are `echo` and `slow_echo` for connectivity and cancellation checks.

## Related

- Front-side repository: [tegnike/aituber-kit](https://github.com/tegnike/aituber-kit)
- Default AITuberKit connection URL: `ws://localhost:8000/ws`

## Features

1. Receive messages from AITuberKit through WebSocket
2. Support both `legacy (v1 compatible)` and `v2` message formats
3. Send server capabilities with `session.ready` immediately after connection
4. Stream `chat.message` responses as `chat.start` / `chat.delta` / `chat.done`
5. Return `ack` when a request is accepted
6. Respond to heartbeat with `ping` / `pong`
7. Cancel the active agent stream task with `control.cancel`
8. Send messages to connected AITuberKit clients from `POST /send_message`
9. Swap the response generator through the `AgentBackend` interface

## Running

### Docker

```bash
docker-compose up -d --build
```

Select a backend:

```bash
AITUBER_SERVER_BACKEND=slow_echo docker-compose up -d --build
```

Stop:

```bash
docker-compose down
```

### Local Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `AITUBER_SERVER_BACKEND` | `echo` | Agent backend. `echo` or `slow_echo` |
| `DEBUG_MODE` | unset | Enables VS Code debug wait when set to `1` |

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET` | `/` | Health check |
| `WS` | `/ws` | WebSocket connection with AITuberKit |
| `POST` | `/send_message` | Send a server initiated message to connected AITuberKit clients |

WebSocket endpoint:

```text
ws://127.0.0.1:8000/ws
```

## WebSocket Integration

Immediately after connection, the server sends `session.ready`. When AITuberKit detects this event, it switches outgoing messages to the `v2` protocol.

`session.ready` includes server capabilities in `payload.capabilities`.

```json
{
  "version": "2",
  "type": "session.ready",
  "payload": {
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
      "character.response.done"
    ]
  }
}
```

AITuberKit sends `session.hello` after receiving `session.ready`. The server returns `ack` for `session.hello`.

## v2 Protocol

In `v2`, every message uses a shared envelope. The wire value of `version` remains the string `"2"` for compatibility.

```json
{
  "version": "2",
  "id": "msg_client_001",
  "type": "chat.message",
  "sessionId": "session_client_001",
  "timestamp": "2026-06-20T00:00:00.000Z",
  "payload": {
    "text": "Hello",
    "image": "data:image/png;base64,..."
  },
  "metadata": {}
}
```

Main events:

| type | Direction | Description |
| ---- | --------- | ----------- |
| `session.ready` | server -> client | Server readiness and capabilities |
| `session.hello` | client -> server | Client capability announcement |
| `chat.message` | client -> server | User input |
| `chat.start` | server -> client | Response start |
| `chat.delta` | server -> client | Streaming response chunk |
| `chat.done` | server -> client | Response completed |
| `chat.error` | server -> client | Request-level error |
| `ack` | server -> client | Request accepted |
| `ping` / `pong` | bidirectional | Heartbeat |
| `control.cancel` | client -> server | Cancel the active task |
| `file.upload` | client -> server | File upload |
| `character.message.received` | client -> server | AITuberKit received a server response |
| `character.message.rendered` | client -> server | AITuberKit rendered the response in chat |
| `character.speech.start` | client -> server | Speech processing started |
| `character.speech.done` | client -> server | Speech segment completed |
| `character.speech.error` | client -> server | Speech processing error |
| `character.response.done` | client -> server | All speech for the response completed |

### chat.message

This is the client input event. The server returns `ack` immediately and passes the payload to the agent backend.

```json
{
  "version": "2",
  "id": "msg_client_001",
  "type": "chat.message",
  "sessionId": "session_client_001",
  "timestamp": "2026-06-20T00:00:00.000Z",
  "payload": {
    "text": "Hello"
  }
}
```

### Streaming Response

The server responds in this order:

1. `chat.start`
2. `chat.delta`
3. `chat.done`

```json
{
  "version": "2",
  "type": "chat.delta",
  "requestId": "msg_client_001",
  "payload": {
    "text": "Echo: Hello"
  }
}
```

`requestId` should match the original `chat.message.id`.

### AITuberKit Lifecycle Events

`chat.done` means that response generation on the server has finished. It does not mean that TTS synthesis, audio playback, lip-sync, or rendering in AITuberKit has finished.

If the server needs to trigger the next action after the character finishes speaking, use `character.response.done` sent from AITuberKit.

```json
{
  "version": "2",
  "type": "character.response.done",
  "requestId": "msg_client_001",
  "payload": {
    "requestId": "msg_client_001",
    "speechSegmentCount": 2,
    "completedAt": "2026-06-20T00:00:05.000Z"
  }
}
```

For per-speech control, use `character.speech.start` / `character.speech.done`. The server acknowledges these client lifecycle events and does not generate a normal chat response for them.

### Cancel

When the client sends `control.cancel`, the server forwards cancellation to the active agent stream task.

```json
{
  "version": "2",
  "type": "control.cancel",
  "payload": {
    "requestId": "msg_client_001"
  }
}
```

If cancellation is accepted, the server returns `ack` and then ends the response with `chat.done` containing `cancelled: true`.

```json
{
  "version": "2",
  "type": "chat.done",
  "requestId": "msg_client_001",
  "payload": {
    "requestId": "msg_client_001",
    "cancelled": true
  }
}
```

## Legacy Format

The legacy JSON format is still accepted for compatibility.

```json
{
  "content": "Hello",
  "type": "chat",
  "image": "data:image/png;base64,..."
}
```

The server normalizes this format to a `chat.message` event internally. Legacy clients still receive JSON with `text`, `role`, `emotion`, and `type`.

```json
{
  "text": "Echo: Hello",
  "role": "assistant",
  "emotion": "neutral",
  "type": ""
}
```

## POST /send_message

Send a message from HTTP to connected AITuberKit clients.

```bash
curl -X POST http://127.0.0.1:8000/send_message \
  -H 'Content-Type: application/json' \
  -d '{"message":"Notification from server"}'
```

Internally, this is handled as a `server.message` event and expanded based on the connected client protocol.

- `v2` client: `chat.start` / `chat.delta` / `chat.done`
- Legacy client: legacy `type: start` / normal message / `type: end`

## Agent Backend

The response generator is separated behind the `AgentBackend` interface.

Available backends:

| backend | Purpose |
| ------- | ------- |
| `echo` | Default. Returns received text as `Echo: ...` |
| `slow_echo` | Cancellation test backend. Emits the first response chunk, then waits for cancel |

Select a backend:

```bash
AITUBER_SERVER_BACKEND=echo docker-compose up -d --build
```

Unknown backend names fall back to `echo`.

## Implementation Map

| File | Role |
| ---- | ---- |
| `app/protocol.py` | `v2` envelope, ack generation, legacy input normalization |
| `app/connection_manager.py` | Connection list, protocol version, `session.ready`, broadcast management |
| `app/services/websocket_session_service.py` | Incoming message dispatch, ack, ping/pong, cancel, backend stream execution |
| `app/services/websocket_service.py` | Legacy / `v2` response sending and server initiated message expansion |
| `app/agent_backends.py` | `AgentBackend`, `echo`, `slow_echo` |
| `app/routers/base.py` | HTTP / WebSocket routes |

## Verification

```bash
python -m pytest
python -m compileall app tests
docker-compose build web
```

Use the `slow_echo` backend when you need to verify `control.cancel`.

## Debugging

1. When using VS Code, start with `DEBUG_MODE=1`.
2. Set breakpoints as needed.

Reference: [VS Code Editor Introduction](https://zenn.dev/karaage0703/books/80b6999d429abc8051bb/viewer/898591)
