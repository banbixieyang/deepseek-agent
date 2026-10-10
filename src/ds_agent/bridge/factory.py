# 后端工厂。按配置创建对应 BrainBackend 实例。
#
# 支持：
#   - api（DeepSeek 官方 API，默认）
#   - web（浏览器自动化，需显式确认风险）
#   - openai（OpenAI 兼容）
#   - ollama（本地 Ollama）
from __future__ import annotations

from ds_agent.bridge.base import BackendError, BrainBackend, RiskNotAcknowledgedError
from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


RISK_TEXT = """
============================================================
  高风险模式提示：网页自动化
============================================================
  本模式通过浏览器自动化操作 DeepSeek 网页版，
  可能违反 DeepSeek 服务条款，存在账号被封禁的风险。

  · 仅限个人学习研究，禁止商用、批量、绕过付费。
  · 请使用小号或专用账号，不要用主力账号。
  · 请控制调用频率，避免高频或并发请求。
  · 使用后果由使用者自行承担。

  如需关闭风险提示，请在 config/config.yaml 中设置：
    backend.web.acknowledge_risk: true
============================================================
"""


def _build_api(cfg: AppConfig) -> BrainBackend:
    provider = (cfg.backend.api.provider or "deepseek").strip().lower()
    if provider == "deepseek":
        from ds_agent.bridge.api.deepseek import DeepSeekAPIBackend

        return DeepSeekAPIBackend(cfg)
    if provider == "openai":
        from ds_agent.bridge.api.openai_compat import OpenAICompatBackend

        return OpenAICompatBackend(cfg)
    if provider == "ollama":
        from ds_agent.bridge.api.ollama import OllamaBackend

        return OllamaBackend(cfg)
    raise BackendError("未知 api.provider：" + provider)


def _build_web(cfg: AppConfig) -> BrainBackend:
    web = cfg.backend.web
    if not web.enabled:
        raise RiskNotAcknowledgedError(
            "网页后端未启用。请在 config/config.yaml 设置 backend.web.enabled: true" + RISK_TEXT
        )
    if not web.acknowledge_risk:
        raise RiskNotAcknowledgedError(
            "未确认网页后端风险。请设置 backend.web.acknowledge_risk: true" + RISK_TEXT
        )
    from ds_agent.bridge.web.deepseek import DeepSeekWebBackend

    return DeepSeekWebBackend(cfg)


def create_backend(cfg: AppConfig) -> BrainBackend:
    # 按 backend.type 创建后端。
    kind = (cfg.backend.type or "api").strip().lower()
    logger.info("创建后端：%s", kind)
    if kind == "api":
        return _build_api(cfg)
    if kind == "web":
        backend = _build_web(cfg)
        logger.warning("[WEB] 当前处于网页自动化高风险模式，请遵守 DeepSeek 服务条款")
        return backend
    if kind == "openai":
        cfg.backend.api.provider = "openai"
        return _build_api(cfg)
    if kind == "ollama":
        cfg.backend.api.provider = "ollama"
        return _build_api(cfg)
    raise BackendError("未知 backend.type：" + kind + "（可选：api / web / openai / ollama）")
