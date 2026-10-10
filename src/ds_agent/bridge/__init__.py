# 桥接层：统一 BrainBackend 接口 + 多后端实现。
#
# 上层（executor）只应通过 create_backend(cfg) 获取后端。
from ds_agent.bridge.base import (
    BackendError,
    BrainBackend,
    RiskNotAcknowledgedError,
)
from ds_agent.bridge.factory import RISK_TEXT, create_backend

__all__ = [
    "RISK_TEXT",
    "BackendError",
    "BrainBackend",
    "RiskNotAcknowledgedError",
    "create_backend",
]
