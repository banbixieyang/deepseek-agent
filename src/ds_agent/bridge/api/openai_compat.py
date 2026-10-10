# OpenAI 兼容后端（预留扩展）。
#
# 与 DeepSeekAPIBackend 共用 /chat/completions 协议，
# 只是 base_url / model 不同。
from __future__ import annotations

import os

from ds_agent.bridge.api.deepseek import DeepSeekAPIBackend
from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


class OpenAICompatBackend(DeepSeekAPIBackend):
    # 兼容 OpenAI Chat Completions 的服务。

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__(cfg)
        # 允许从通用环境变量读取
        if not self._api_key:
            self._api_key = (os.environ.get("OPENAI_API_KEY", "")).strip()

    @property
    def kind(self) -> str:
        return "openai"
