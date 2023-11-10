# Beautiful Girl OpenInterpreter
[Japanese version](./README.md)

## Note

- (16/10/2023) I'm currently pinned to version 0.1.7 of Open Interpreter due to an error in the latest version (0.1.9) that prevents WebSocket from sending in chunks.
- (16/10/2023) I changed repository name from "nike-open-intepreter" to "nike-open-interpreter" because of misspelling.
- (11/11/2023) I removed version 0.1.7 pinned of Open Interpreter because I could check it works correctly in the latest version (0.1.13).

## Relation

- Front-side repository -> [tegnike/nike-ChatVRM](https://github.com/tegnike/nike-ChatVRM)

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
