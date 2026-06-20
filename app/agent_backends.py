import os
import time
from typing import Dict, Iterable, Protocol


class AgentBackend(Protocol):
    def prepare(self) -> None:
        ...

    def stream(self, message: str) -> Iterable[Dict]:
        ...

    def cancel(self) -> None:
        ...


class EchoAgentBackend:
    def prepare(self) -> None:
        return

    def stream(self, message: str) -> Iterable[Dict]:
        yield {"type": "message", "content": f"Echo: {message}"}

    def cancel(self) -> None:
        return


class SlowEchoAgentBackend:
    def __init__(self):
        self.cancelled = False

    def prepare(self) -> None:
        self.cancelled = False

    def stream(self, message: str) -> Iterable[Dict]:
        yield {"type": "message", "content": f"SlowEcho: {message}。"}
        yield {"type": "message", "content": " "}
        while not self.cancelled:
            time.sleep(0.05)

    def cancel(self) -> None:
        self.cancelled = True


def create_agent_backend(language: str) -> AgentBackend:
    backend_name = os.getenv("AITUBER_SERVER_BACKEND", "echo").lower()
    if backend_name == "echo":
        return EchoAgentBackend()
    if backend_name == "slow_echo":
        return SlowEchoAgentBackend()
    return EchoAgentBackend()
