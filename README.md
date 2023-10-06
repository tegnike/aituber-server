# 美少女OPInterpreter 公開用
[English version](./en_README.md)

## できること

1. WebSocketでメッセージを受け取って、Open Interpreterからレスポンスを取得することができます（streamモード対応）。
2. ファイルを送信してサーバー側に保存することができます。このファイルに対してOpen Interpreterに指示を出すことも可能です。

## 事前準備

1. 本リポジトリはWebSocketでの起動を前提としているため、ご自身の環境に合わせて接続先を準備してください。
2. 接続URLはデフォルトで`ws://127.0.0.1:8000/ws`です。

## 実行方法

1. `.env`にOPENAI_API_KEYを設定
2. `docker-compose up -d --build` 実行

## デバッグ

1. 実行環境がVSCodeのときに、DEBUG_MODE=1でデバッグモードを起動します。
2. ブレークポイントを設置して快適にデバッグしましょう。

参考: [VS Codeエディタ入門](https://zenn.dev/karaage0703/books/80b6999d429abc8051bb/viewer/898591)

## コード解説

長くなるので下記に記載しました。

- [【コード解説】美少女OPInterpreter簡易版](https://note.com/nike_cha_n/n/n39f62ee846e3)

## その他

1. ライセンスは[KillianLucas/open-interpreter](https://github.com/KillianLucas/open-interpreter)に準拠します。
2. Open Interpreterの使用方法は下記にまとめています。

- [【開発者向け】Open Interpreterの使い方をコード付きで説明する（python編）](https://note.com/nike_cha_n/n/n764514cf5351)
