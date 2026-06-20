# AITuberKit サーバーサイド

[English version](./en_README.md)

## 概要

AITuberKitの外部連携モード用WebSocket serverです。

AITuberKit本体は、チャット表示、音声合成、キャラクター表示、表情・モーション制御を担当します。このserverは、AITuberKitと外部処理をつなぐWebSocket protocol serverとして動作します。

従来のlegacy JSON形式を `legacy (v1互換)` として維持しつつ、現在は `v2` WebSocket protocol、`ack`、heartbeat、cancel、server initiated messageに対応しています。`v1` という独立した新protocolはなく、従来JSON互換がlegacyです。

Open Interpreter依存は削除済みです。応答生成は `AgentBackend` interface の背後に分離され、現在は疎通確認用の `echo` / `slow_echo` backendを提供します。

## 関連

- フロントサイドリポジトリ: [tegnike/aituber-kit](https://github.com/tegnike/aituber-kit)
- AITuberKit側の既定接続URL: `ws://localhost:8000/ws`

## できること

1. AITuberKitからWebSocketでmessageを受け取る
2. `legacy (v1互換)` 形式と `v2` 形式の両方を扱う
3. 接続直後に `session.ready` でserver capabilitiesを通知する
4. `chat.message` を `chat.start` / `chat.delta` / `chat.done` としてstream応答する
5. `ack` でrequest受理を返す
6. `ping` / `pong` でheartbeatに応答する
7. `control.cancel` で実行中のagent stream taskを中断する
8. `POST /send_message` から接続中のAITuberKitへmessageを送る
9. `AgentBackend` を差し替えて応答生成部分を別実装にできる

## 起動方法

### Docker

```bash
docker-compose up -d --build
```

backendを指定する場合:

```bash
AITUBER_SERVER_BACKEND=slow_echo docker-compose up -d --build
```

停止:

```bash
docker-compose down
```

### ローカルPython

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 環境変数

| 変数 | 既定値 | 内容 |
| ---- | ------ | ---- |
| `AITUBER_SERVER_BACKEND` | `echo` | 使用するagent backend。`echo` または `slow_echo` |
| `DEBUG_MODE` | 未設定 | `1` のときVS Code向けdebug待受を有効化 |

## Endpoint

| Method | Path | 内容 |
| ------ | ---- | ---- |
| `GET` | `/` | health check |
| `WS` | `/ws` | AITuberKitとのWebSocket接続 |
| `POST` | `/send_message` | 接続中のAITuberKitへserver initiated messageを送信 |

WebSocket endpoint:

```text
ws://127.0.0.1:8000/ws
```

## WebSocket連携

接続直後、serverは `session.ready` を送信します。AITuberKit側はこのeventを検知すると、以後の送信を `v2` protocolに切り替えます。

`session.ready` の `payload.capabilities` には、serverが扱える機能を含めます。

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

AITuberKitは `session.ready` を受けると `session.hello` を返します。serverは `session.hello` に対して `ack` を返します。

## v2 protocol

`v2` では、すべてのmessageを共通envelopeで扱います。wire上の `version` 値は互換性のため文字列の `"2"` です。

```json
{
  "version": "2",
  "id": "msg_client_001",
  "type": "chat.message",
  "sessionId": "session_client_001",
  "timestamp": "2026-06-20T00:00:00.000Z",
  "payload": {
    "text": "こんにちは",
    "image": "data:image/png;base64,..."
  },
  "metadata": {}
}
```

主なevent:

| type | 方向 | 内容 |
| ---- | ---- | ---- |
| `session.ready` | server -> client | server準備完了とcapabilities通知 |
| `session.hello` | client -> server | client側の機能通知 |
| `chat.message` | client -> server | ユーザー入力 |
| `chat.start` | server -> client | 応答開始 |
| `chat.delta` | server -> client | stream応答断片 |
| `chat.done` | server -> client | 応答終了 |
| `chat.error` | server -> client | 応答単位のエラー |
| `ack` | server -> client | request受理通知 |
| `ping` / `pong` | 双方向 | heartbeat |
| `control.cancel` | client -> server | 実行中処理のキャンセル |
| `file.upload` | client -> server | ファイル送信 |
| `character.message.received` | client -> server | AITuberKitがserver応答を受信 |
| `character.message.rendered` | client -> server | AITuberKitが応答をチャット表示へ反映 |
| `character.speech.start` | client -> server | 発話処理開始 |
| `character.speech.done` | client -> server | 発話セグメント完了 |
| `character.speech.error` | client -> server | 発話処理エラー |
| `character.response.done` | client -> server | 応答全体の発話完了 |

### chat.message

clientからの入力です。serverは受信直後に `ack` を返し、agent backendへ渡します。

```json
{
  "version": "2",
  "id": "msg_client_001",
  "type": "chat.message",
  "sessionId": "session_client_001",
  "timestamp": "2026-06-20T00:00:00.000Z",
  "payload": {
    "text": "こんにちは"
  }
}
```

### stream応答

serverは次の順で応答します。

1. `chat.start`
2. `chat.delta`
3. `chat.done`

```json
{
  "version": "2",
  "type": "chat.delta",
  "requestId": "msg_client_001",
  "payload": {
    "text": "Echo: こんにちは"
  }
}
```

`requestId` は元の `chat.message.id` と一致させます。

### AITuberKit lifecycle events

`chat.done` はserver側の応答生成完了です。AITuberKit側のTTS合成、音声再生、口パク、表示処理の完了とは別です。

server側で「キャラクターが喋り終わった後に次の行動をする」場合は、AITuberKitから送られる `character.response.done` をトリガーにしてください。

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

発話文ごとの制御が必要な場合は、`character.speech.start` / `character.speech.done` を使います。serverはこれらのclient lifecycle eventを受け取ると `ack` だけ返し、通常のchat応答は生成しません。

### cancel

clientが `control.cancel` を送ると、serverは実行中のagent stream taskへキャンセルを伝えます。

```json
{
  "version": "2",
  "type": "control.cancel",
  "payload": {
    "requestId": "msg_client_001"
  }
}
```

キャンセルを受理した場合、serverは `ack` を返し、最終的に `chat.done` に `cancelled: true` を含めます。

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

## legacy形式

既存clientとの互換のため、従来のJSON形式も引き続き受け付けます。

```json
{
  "content": "こんにちは",
  "type": "chat",
  "image": "data:image/png;base64,..."
}
```

server内部では、この形式を `chat.message` eventへ正規化して処理します。legacy clientに対しては、従来通り `text`、`role`、`emotion`、`type` を持つJSONを返します。

```json
{
  "text": "Echo: こんにちは",
  "role": "assistant",
  "emotion": "neutral",
  "type": ""
}
```

## POST /send_message

HTTPから接続中のAITuberKitへmessageを送ります。

```bash
curl -X POST http://127.0.0.1:8000/send_message \
  -H 'Content-Type: application/json' \
  -d '{"message":"serverからの通知"}'
```

内部では `server.message` eventとして扱い、接続protocolに応じて次のように展開します。

- `v2` client: `chat.start` / `chat.delta` / `chat.done`
- legacy client: 従来の `type: start` / 通常message / `type: end`

## Agent backend

応答生成部分は `AgentBackend` interface に分離しています。

現在のbackend:

| backend | 用途 |
| ------- | ---- |
| `echo` | 既定。受け取ったmessageを `Echo: ...` として返す |
| `slow_echo` | cancel確認用。最初の応答chunkを返したあと、cancelまで待つ |

backendの選択:

```bash
AITUBER_SERVER_BACKEND=echo docker-compose up -d --build
```

未知のbackend名が指定された場合は `echo` にfallbackします。

## 実装構成

| ファイル | 役割 |
| -------- | ---- |
| `app/protocol.py` | `v2` envelope、ack生成、legacy入力正規化 |
| `app/connection_manager.py` | 接続一覧、protocol version、`session.ready`、broadcast管理 |
| `app/services/websocket_session_service.py` | 受信message dispatch、ack、ping/pong、cancel、backend stream実行 |
| `app/services/websocket_service.py` | legacy / `v2` 応答送信、server initiated message展開 |
| `app/agent_backends.py` | `AgentBackend`、`echo`、`slow_echo` |
| `app/routers/base.py` | HTTP / WebSocket route |

## 検証

```bash
python -m pytest
python -m compileall app tests
docker-compose build web
```

`slow_echo` backendを使うと、`control.cancel` の疎通確認がしやすくなります。

## デバッグ

1. 実行環境がVS Codeのときに、`DEBUG_MODE=1`でデバッグモードを起動します
2. ブレークポイントを設置してデバッグできます

参考: [VS Codeエディタ入門](https://zenn.dev/karaage0703/books/80b6999d429abc8051bb/viewer/898591)
