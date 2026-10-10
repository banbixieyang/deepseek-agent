# Ollama 本地后端（预留扩展，可选）。
#
# 通过 Ollama 的 OpenAI 兼容接口调用本地模型。
from __future__ import annotations

from ds_agent.bridge.api.deepseek import DeepSeekAPIBackend
from ds_agent.bridge.base import BackendError
from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


class OllamaBackend(DeepSeekAPIBackend):
    # 本地 Ollama 后端。

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__(cfg)
        # Ollama 不需要 API Key
        if not self._api_key:
            self._api_key = "ollama"

    @property
    def kind(self) -> str:
        return "ollama"

    def start(self) -> None:
        # 只做日志与连通性探测，不阻塞。
        logger.info("后端启动：Ollama（model=%s, base_url=%s）", self._model, self._base_url)
        try:
            self._chat([{"role": "user", "content": "ping"}], timeout=5.0)
            logger.info("Ollama 连通性测试通过")
        except BackendError as exc:
            logger.warning("Ollama 连通性测试失败（不阻塞启动）：%s", exc)
