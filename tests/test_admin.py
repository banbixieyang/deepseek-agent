# 管理面板逻辑测试（不启动 uvicorn，直接调用 create_app）。
from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")

from ds_agent import admin  # noqa: E402


def test_create_app_returns_app_and_password(isolated_config):
    app, password = admin.create_app(password="testpass")
    assert password == "testpass"
    assert app is not None
    assert app.state.admin_password == "testpass"


def test_create_app_generates_password_when_absent(isolated_config, monkeypatch):
    monkeypatch.delenv("DS_AGENT_ADMIN_PASSWORD", raising=False)
    _app, password = admin.create_app()
    assert isinstance(password, str) and len(password) >= 8


def test_render_form_contains_backend_select(isolated_config):
    html = admin._render_form(isolated_config)
    assert "后端选择" in html
    assert "web" in html
    assert "api" in html


def test_render_form_shows_risk_banner(isolated_config):
    html = admin._render_form(isolated_config)
    assert "风险" in html
