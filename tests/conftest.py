# pytest 通用 fixture。
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# 确保 src/ 在 sys.path 中。
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for p in (str(SRC), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture()
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # 生成一套隔离配置：工作区/备份/日志都在 tmp_path 下。
    from ds_agent import config as config_module
    from ds_agent.schema import AppConfig

    cfg = AppConfig()
    cfg.paths.workspace_dir = str(tmp_path / "workspace")
    cfg.paths.internal_dir = str(tmp_path / "_internal")
    cfg.paths.backup_dir = str(tmp_path / "_internal" / "backups")
    cfg.paths.log_dir = str(tmp_path / "_internal" / "logs")
    cfg.backend.type = "api"
    cfg.backend.api.api_key = "test-key"

    config_module.set_config(cfg)
    try:
        yield cfg
    finally:
        config_module.set_config(AppConfig())
