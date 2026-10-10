# 配置加载、保存与路径解析。
#
# import 本模块不产生副作用：不创建目录、不读文件、不访问网络。
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from ds_agent.schema import AppConfig, from_dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
EXAMPLE_CONFIG_PATH = CONFIG_DIR / "config.example.yaml"


def project_root() -> Path:
    return PROJECT_ROOT


def config_path() -> Path:
    env = os.environ.get("DS_AGENT_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    return DEFAULT_CONFIG_PATH


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def load_config(path: Any | None = None) -> AppConfig:
    # 加载配置：指定路径 > config.yaml > config.example.yaml，再叠加环境变量。
    target = Path(path) if path else config_path()
    data = _read_yaml(target)
    if not data and target != EXAMPLE_CONFIG_PATH:
        data = _read_yaml(EXAMPLE_CONFIG_PATH)
    cfg = from_dict(data)
    apply_env(cfg)
    return cfg


def save_config(cfg: AppConfig, path: Any | None = None) -> Path:
    target = Path(path) if path else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        yaml.safe_dump(cfg.to_dict(), f, allow_unicode=True, sort_keys=False)
    return target


# env 名 -> (配置段, 字段名)；段为 None 表示顶层字段。
_ENV_MAP = {
    "DS_AGENT_BACKEND": ("backend", "type"),
    "DEEPSEEK_API_KEY": ("backend.api", "api_key"),
    "DEEPSEEK_BASE_URL": ("backend.api", "base_url"),
    "DEEPSEEK_MODEL": ("backend.api", "model"),
    "DS_AGENT_DRIVER": ("driver", "type"),
    "DS_AGENT_WORKSPACE_DIR": ("paths", "workspace_dir"),
    "DS_AGENT_DS_READ_SCRIPT": ("backend.web", "ds_read_script"),
    "DS_AGENT_SESSION_ID": ("backend.web", "session_id"),
    "DS_AGENT_LOG_LEVEL": ("logging", "level"),
    "DS_AGENT_OLLAMA_HOST": (None, "ollama_host"),
}


def apply_env(cfg: AppConfig) -> AppConfig:
    # 用环境变量覆盖配置字段。空字符串视为未设置。
    for env_key, (section, attr) in _ENV_MAP.items():
        value = os.environ.get(env_key)
        if value in (None, ""):
            continue
        if section is None:
            setattr(cfg, attr, value)
            continue
        target: Any = cfg
        for part in section.split("."):
            target = getattr(target, part)
        setattr(target, attr, value)
    return cfg


_cached: AppConfig | None = None


def get_config(reload: bool = False) -> AppConfig:
    global _cached
    if _cached is None or reload:
        _cached = load_config()
    return _cached


def set_config(cfg: AppConfig) -> AppConfig:
    global _cached
    _cached = cfg
    return _cached


def resolve_path(value: str) -> Path:
    # 相对路径基于项目根目录。
    if not value:
        return PROJECT_ROOT
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()


def ensure_directories(cfg: AppConfig) -> None:
    for key in ("workspace_dir", "internal_dir", "backup_dir", "log_dir"):
        resolve_path(getattr(cfg.paths, key)).mkdir(parents=True, exist_ok=True)
