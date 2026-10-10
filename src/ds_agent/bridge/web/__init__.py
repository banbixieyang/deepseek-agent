# 网页自动化后端（高风险，默认关闭）。
#
# 使用前必须在 config/config.yaml 中设置：
#   backend.type: web
#   backend.web.enabled: true
#   backend.web.acknowledge_risk: true
# 否则启动时会直接拒绝。
from ds_agent.bridge.web.browser import (
    BrowserDriver,
    PyAutoGUIDriver,
    WindowInfo,
    create_driver,
)
from ds_agent.bridge.web.deepseek import DeepSeekWebBackend
from ds_agent.bridge.web.ds_read import DsReadClient, DsReadError

__all__ = [
    "BrowserDriver",
    "DeepSeekWebBackend",
    "DsReadClient",
    "DsReadError",
    "PyAutoGUIDriver",
    "WindowInfo",
    "create_driver",
]
