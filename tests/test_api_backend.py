# DeepSeek API 后端测试（mock requests，不联网）。
from __future__ import annotations

from typing import Any

import pytest

from ds_agent.bridge.api.deepseek import DeepSeekAPIBackend
from ds_agent.bridge.base import BackendError
from ds_agent.schema import AppConfig


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = "fake"

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeRequests:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._responses = list(responses)

    def post(
        self, url: str, headers: dict[str, str], json: dict[str, Any], timeout: float
    ) -> _FakeResponse:
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return self._responses.pop(0)


@pytest.fixture()
def cfg():
    c = AppConfig()
    c.backend.api.api_key = "test-key"
    c.backend.api.min_interval_seconds = 0.0
    c.backend.api.retry = 1
    c.approval.send_to_deepseek = False
    return c


def _patch_requests(monkeypatch, fake: _FakeRequests):
    import sys
    import types

    module = types.ModuleType("requests")
    module.post = fake.post  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "requests", module)


def test_ask_returns_content(monkeypatch, cfg):
    fake = _FakeRequests(
        [_FakeResponse(200, {"choices": [{"message": {"content": "hello"}}], "id": "c1"})]
    )
    _patch_requests(monkeypatch, fake)
    backend = DeepSeekAPIBackend(cfg)
    reply = backend.ask("hi")
    assert reply == "hello"
    assert backend.session_id == "c1"
    assert len(backend._messages) == 2


def test_new_conversation_clears_messages(monkeypatch, cfg):
    fake = _FakeRequests([_FakeResponse(200, {"choices": [{"message": {"content": "a"}}]})])
    _patch_requests(monkeypatch, fake)
    backend = DeepSeekAPIBackend(cfg)
    backend.ask("hi")
    backend.new_conversation()
    assert backend._messages == []


def test_ask_raises_on_missing_key(monkeypatch, cfg):
    cfg.backend.api.api_key = ""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    backend = DeepSeekAPIBackend(cfg)
    with pytest.raises(BackendError):
        backend.start()


def test_ask_rejects_on_4xx(monkeypatch, cfg):
    fake = _FakeRequests([_FakeResponse(401, {})])
    _patch_requests(monkeypatch, fake)
    backend = DeepSeekAPIBackend(cfg)
    with pytest.raises(BackendError):
        backend.ask("hi")
    # 失败时 messages 不应残留用户消息
    assert backend._messages == []


def test_ask_retries_on_5xx(monkeypatch, cfg):
    cfg.backend.api.retry = 2
    fake = _FakeRequests(
        [
            _FakeResponse(500, {}),
            _FakeResponse(200, {"choices": [{"message": {"content": "ok"}}]}),
        ]
    )
    _patch_requests(monkeypatch, fake)
    # 把退避时间改为 0 避免测试变慢
    monkeypatch.setattr("time.sleep", lambda *_: None)
    backend = DeepSeekAPIBackend(cfg)
    assert backend.ask("hi") == "ok"
