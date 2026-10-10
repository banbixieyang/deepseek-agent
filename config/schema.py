# 兼容层：真正的数据模型在 src/ds_agent/schema.py。
#
# 保留本文件是为了让 config/ 目录自解释，同时不破坏包内导入路径。
# 使用前请确保 src/ 在 sys.path 中（根目录 app.py 会自动处理）。
from ds_agent.schema import (  # noqa: F401
    AppConfig,
    ApprovalConfig,
    AttachConfig,
    DeepSeekConfig,
    DriverConfig,
    HumanConfig,
    LoggingConfig,
    LoopConfig,
    PathsConfig,
    from_dict,
)

__all__ = [
    "AppConfig",
    "ApprovalConfig",
    "AttachConfig",
    "DeepSeekConfig",
    "DriverConfig",
    "HumanConfig",
    "LoggingConfig",
    "LoopConfig",
    "PathsConfig",
    "from_dict",
]
