# 美少女OPInterpreter 服务器端 公开版

[ [Japanese version](./README.md) | [English version](./en_README.md) | [简体中文版本](./zh_README.md) ]

## 注意

- (2023/10/16) 由于最新版本的 Open Interpreter (0.1.9) 出现了 WebSocket 无法按块发送的错误，因此暂时固定在 0.1.7 版本。
- (2023/10/16) 修正了仓库名称的拼写错误。"nike-open-intepreter" => "nike-open-interpreter"
- (2023/11/11) 确认最新版本的 Open Interpreter (0.1.13) 已经解决了 WebSocket 错误，因此解除了版本固定。

## 相关

- 前端仓库 -> [tegnike/nike-ChatVRM](https://github.com/tegnike/nike-ChatVRM)

## 功能

1. 可以通过 WebSocket 接收消息，并从 Open Interpreter 获取响应（支持 stream 模式）。
2. 可以发送文件并保存在服务器端，也可以向 Open Interpreter 指示处理这些文件。

## 事前准备

1. 本仓库假设通过 WebSocket 启动，请根据您的环境准备连接地址。
2. 默认连接 URL 为 `ws://127.0.0.1:8000/ws`。

## 运行方法

1. 在 `.env` 文件中设置 OPENAI_API_KEY。
2. 执行 `docker-compose up -d --build`。

## 调试

1. 如果在 VSCode 中运行环境，设置 DEBUG_MODE=1 以启动调试模式。
2. 设置断点进行舒适的调试。

参考: [VS Code 编辑器入门](https://zenn.dev/karaage0703/books/80b6999d429abc8051bb/viewer/898591)

## 代码解说

由于篇幅较长，请参考以下链接。

- [【代码解说】美少女OPInterpreter 简易版](https://note.com/nike_cha_n/n/n39f62ee846e3)

## 其他

1. 许可证遵循 [KillianLucas/open-interpreter](https://github.com/KillianLucas/open-interpreter)。
2. Open Interpreter 的使用方法总结在下方链接。

- [【开发者向】Open Interpreter 的使用方法（Python 篇）](https://note.com/nike_cha_n/n/n764514cf5351)

