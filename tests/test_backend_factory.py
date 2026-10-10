# 后端工厂与风险确认门测试。
from __future__ import annotations

import pytest

from ds_agent.bridge.base import BackendError, RiskNotAcknowledgedError
from ds_agent.bridge.factory import create_backend
from ds_agent.schema import AppConfig


def test_default_backend_is_api():
    cfg = AppConfig()
    assert cfg.backend.type == "api"
    backend = create_backend(cfg)
    assert backend.kind == "api"


def test_web_without_enable_raises():
    cfg = AppConfig()
    cfg.backend.type = "web"
    with pytest.raises(RiskNotAcknowledgedError):
        create_backend(cfg)


def test_web_without_acknowledge_raises():
    cfg = AppConfig()
    cfg.backend.type = "web"
    cfg.backend.web.enabled = True
    with pytest.raises(RiskNotAcknowledgedError):
        create_backend(cfg)


def test_unknown_backend_type_raises():
    cfg = AppConfig()
    cfg.backend.type = "nope"
    with pytest.raises(BackendError):
        create_backend(cfg)
