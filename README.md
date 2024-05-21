# 美少女OPInterpreter サーバーサイド 公開用

[ [Japanese version](./README.md) | [English version](./en_README.md) | [简体中文版本](./zh_README.md) ]

## 注意

- (2023/10/16) Open Interpreterの最新のバージョン（0.1.9）で、WebSocketがchunk毎に送信できないエラーが発生したので、一旦0.1.7で固定しています。
- (2023/10/16) リポジトリ名のスペルが誤っていたので修正しました。"nike-open-intepreter" => "nike-open-interpreter"
- (2023/11/11) Open Interpreterの最新のバージョン（0.1.13）で、WebSocketエラーが解消していたことを確認したので、バージョンの固定を解除しました。

## 関連

- フロントサイドリポジトリ -> [tegnike/nike-ChatVRM](https://github.com/tegnike/nike-ChatVRM)

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
