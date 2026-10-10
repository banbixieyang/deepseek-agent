# 配置数据模型。
#
# 只描述结构与默认值，不产生任何副作用：不创建目录、不读文件、不访问网络。
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


@dataclass
class APIConfig:
    # API 后端配置（DeepSeek / OpenAI 兼容 / Ollama）。
    provider: str = "deepseek"
    # 留空时读环境变量 DEEPSEEK_API_KEY（或 provider 对应的通用变量）
    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: float = 120.0
    retry: int = 3
    min_interval_seconds: float = 1.0


@dataclass
class WebBackendConfig:
    # 网页自动化后端配置。默认全部关闭，必须显式确认。
    enabled: bool = False
    acknowledge_risk: bool = False
    ds_read_script: str = ""
    # 内置下载地址（可选）。启动器在准备 ds_read.py 时会优先使用它。
    ds_read_url: str = ""
    python_executable: str = "python"
    url: str = "https://chat.deepseek.com"
    window_titles: list[str] = field(default_factory=lambda: ["Mozilla Firefox", "Firefox"])
    session_id: str = ""


@dataclass
class BackendConfig:
    # 后端选择：api | web | openai | ollama
    type: str = "api"
    api: APIConfig = field(default_factory=APIConfig)
    web: WebBackendConfig = field(default_factory=WebBackendConfig)


@dataclass
class DriverConfig:
    # 网页后端使用的驱动：pyautogui | playwright | cdp
    type: str = "pyautogui"
    click_ratio_new_session: float = 0.48
    click_ratio_existing: float = 0.85
    activate_retry_click_offset: int = 100


@dataclass
class PathsConfig:
    workspace_dir: str = "workspace"
    internal_dir: str = "_internal"
    backup_dir: str = "_internal/backups"
    log_dir: str = "_internal/logs"


@dataclass
class LoopConfig:
    max_rounds: int = 200
    max_format_retry: int = 3
    poll_interval: float = 3.0
    reply_timeout: float = 240.0
    stable_required: int = 4
    min_wait: float = 10.0
    batch_approval_threshold: int = 5


@dataclass
class HumanConfig:
    delay_before_send_min: float = 1.5
    delay_before_send_max: float = 3.5
    delay_before_enter_min: float = 0.8
    delay_before_enter_max: float = 2.0
    min_interval_between_messages: float = 5.0


@dataclass
class ApprovalConfig:
    send_to_deepseek: bool = True
    write_file: bool = True
    tools: list[str] = field(
        default_factory=lambda: [
            "write_file",
            "edit_file",
            "append_file",
            "delete_file",
            "move_file",
            "copy_file",
        ]
    )


@dataclass
class AttachConfig:
    max_file_chars: int = 50000
    max_folder_files: int = 100
    max_folder_total_chars: int = 200000
    max_per_file_chars: int = 20000
    skip_dirs: list[str] = field(
        default_factory=lambda: [
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "dist",
            "build",
        ]
    )
    skip_exts: list[str] = field(
        default_factory=lambda: [
            ".exe",
            ".dll",
            ".so",
            ".pyc",
            ".png",
            ".jpg",
            ".zip",
        ]
    )


@dataclass
class LoggingConfig:
    level: str = "INFO"
    to_file: bool = True
    keep_days: int = 7


@dataclass
class AppConfig:
    backend: BackendConfig = field(default_factory=BackendConfig)
    driver: DriverConfig = field(default_factory=DriverConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    loop: LoopConfig = field(default_factory=LoopConfig)
    human: HumanConfig = field(default_factory=HumanConfig)
    approval: ApprovalConfig = field(default_factory=ApprovalConfig)
    attach: AttachConfig = field(default_factory=AttachConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    # 可选，仅诊断页探测
    ollama_host: str = "http://127.0.0.1:11434"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_NESTED: dict[str, Any] = {
    "backend": BackendConfig,
    "driver": DriverConfig,
    "paths": PathsConfig,
    "loop": LoopConfig,
    "human": HumanConfig,
    "approval": ApprovalConfig,
    "attach": AttachConfig,
    "logging": LoggingConfig,
}

_SUB_NESTED: dict[str, dict[str, Any]] = {
    "backend": {
        "api": APIConfig,
        "web": WebBackendConfig,
    },
}


def _build_section(
    cls: Any, data: dict[str, Any] | None, sub_map: dict[str, Any] | None = None
) -> Any:
    # 用 data 覆盖 cls 的默认值，忽略未知字段。
    if not isinstance(data, dict):
        return cls()
    allowed = {f.name for f in fields(cls)}
    kwargs: dict[str, Any] = {}
    for key, value in data.items():
        if key not in allowed:
            continue
        if sub_map and key in sub_map:
            kwargs[key] = _build_section(sub_map[key], value)
        else:
            kwargs[key] = value
    return cls(**kwargs)


def from_dict(data: dict[str, Any] | None) -> AppConfig:
    # 把配置字典递归映射为 AppConfig，未知字段被忽略。
    data = data or {}
    kwargs: dict[str, Any] = {}
    for f in fields(AppConfig):
        if f.name not in data:
            continue
        value = data[f.name]
        nested_cls = _NESTED.get(f.name)
        if nested_cls is not None:
            sub_map = _SUB_NESTED.get(f.name)
            kwargs[f.name] = _build_section(nested_cls, value, sub_map)
        else:
            kwargs[f.name] = value
    return AppConfig(**kwargs)
