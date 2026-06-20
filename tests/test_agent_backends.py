from app.agent_backends import (
    EchoAgentBackend,
    SlowEchoAgentBackend,
    create_agent_backend,
)


def test_echo_agent_backend_streams_echo_message():
    backend = EchoAgentBackend()

    backend.prepare()
    chunks = list(backend.stream("hello"))

    assert chunks == [{"type": "message", "content": "Echo: hello"}]


def test_create_agent_backend_can_select_echo(monkeypatch):
    monkeypatch.setenv("AITUBER_SERVER_BACKEND", "echo")

    backend = create_agent_backend("japanese")

    assert isinstance(backend, EchoAgentBackend)


def test_create_agent_backend_defaults_to_echo(monkeypatch):
    monkeypatch.delenv("AITUBER_SERVER_BACKEND", raising=False)

    backend = create_agent_backend("japanese")

    assert isinstance(backend, EchoAgentBackend)


def test_create_agent_backend_falls_back_to_echo_for_unknown_backend(monkeypatch):
    monkeypatch.setenv("AITUBER_SERVER_BACKEND", "unknown")

    backend = create_agent_backend("japanese")

    assert isinstance(backend, EchoAgentBackend)


def test_create_agent_backend_can_select_slow_echo(monkeypatch):
    monkeypatch.setenv("AITUBER_SERVER_BACKEND", "slow_echo")

    backend = create_agent_backend("japanese")

    assert isinstance(backend, SlowEchoAgentBackend)


def test_slow_echo_agent_backend_stops_when_cancelled():
    backend = SlowEchoAgentBackend()
    backend.prepare()
    stream = backend.stream("hello")

    assert next(stream) == {"type": "message", "content": "SlowEcho: hello。"}
    assert next(stream) == {"type": "message", "content": " "}

    backend.cancel()

    assert list(stream) == []
