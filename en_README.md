# OpenInterpreter with Live2D
[Japanese version](./README.md)

## Features

1. You can receive messages via WebSocket and obtain responses from the Open Interpreter (supports stream mode).
2. You can send files to be saved on the server side. You can also issue commands to the Open Interpreter for these files.

## Prerequisites

1. This repository assumes operation via WebSocket, so please prepare a connection destination suitable for your environment.
2. The default connection URL is `ws://127.0.0.1:8000/ws`.

## Execution Steps

1. Set the OPENAI_API_KEY in `.env`.
2. Execute `docker-compose up -d --build`.

## Debugging

1. When using VSCode as the execution environment, launch in debug mode with DEBUG_MODE=1.
2. Set breakpoints and enjoy comfortable debugging.

Reference: [VS Code Editor Introduction](https://zenn.dev/karaage0703/books/80b6999d429abc8051bb/viewer/898591)

## Code Explanation

It's lengthy, so I've detailed it in the link below:

- https://note.com/nike_cha_n/n/n39f62ee846e3

## Miscellaneous

1. The license conforms to [KillianLucas/open-interpreter](https://github.com/KillianLucas/open-interpreter).
2. Instructions on using the Open Interpreter are consolidated in the link below:

- https://note.com/nike_cha_n/n/n764514cf5351
