# 配置向导测试。
from __future__ import annotations

from ds_agent import config_cli


def test_confirm_risk_accepts_exact_token(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_: "I understand")
    assert config_cli.confirm_risk() is True


def test_confirm_risk_rejects_other_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda *_: "yes")
    assert config_cli.confirm_risk() is False


def test_setup_api_writes_env(monkeypatch, tmp_path, isolated_config):
    monkeypatch.setattr(config_cli, "project_root", lambda: tmp_path)
    answers = iter(["1", "", "secret-key"])
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    cfg = isolated_config
    config_cli.setup_api(cfg)
    env_path = tmp_path / ".env"
    assert env_path.is_file()
    content = env_path.read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY=secret-key" in content


def test_setup_web_sets_flags(monkeypatch, isolated_config):
    answers = iter(["/tmp/ds_read.py", "Firefox"])
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    cfg = isolated_config
    config_cli.setup_web(cfg)
    assert cfg.backend.type == "web"
    assert cfg.backend.web.enabled is True
    assert cfg.backend.web.acknowledge_risk is True
    assert cfg.backend.web.ds_read_script == "/tmp/ds_read.py"


def test_main_exits_when_user_cancels(monkeypatch, isolated_config):
    monkeypatch.setattr("builtins.input", lambda *_: "3")
    assert config_cli.main([]) == 0
