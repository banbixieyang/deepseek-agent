# DeepSeek 官方 API 后端（推荐，默认）。
#
# 特性：
#   - 走 OpenAI 兼容的 /chat/completions
#   - 内部维护 messages，实现多轮对话
#   - 网络错误/5xx 指数退避重试
#   - 内置最小请求间隔，避免触发限流
#   - api_key 只从环境变量 DEEPSEEK_API_KEY 或配置读取，绝不硬编码
from __future__ import annotations

import os
import time
from typing import Any

from ds_agent.bridge.base import BackendError
from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


def _mask(secret: str) -> str:
    if not secret:
        return "(空)"
    if len(secret) <= 4:
        return "****"
    return secret[:4] + "****"


class DeepSeekAPIBackend:
    # 通过 DeepSeek 官方 API 交互。

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        api = cfg.backend.api
        self._api_key = (api.api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
        self._base_url = (api.base_url or "https://api.deepseek.com").rstrip("/")
        self._model = api.model or "deepseek-chat"
        self._temperature = float(api.temperature)
        self._max_tokens = int(api.max_tokens)
        self._timeout = float(api.timeout)
        self._retry = max(1, int(api.retry))
        self._min_interval = max(0.0, float(api.min_interval_seconds))
        self._messages: list[dict[str, str]] = []
        self._last_call = 0.0
        self._session_id: str | None = None

    @property
    def kind(self) -> str:
        return "api"

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def start(self) -> None:
        if not self._api_key:
            raise BackendError(
                "未配置 API Key。请任选其一：\n"
                "  1. 设置环境变量 DEEPSEEK_API_KEY\n"
                "  2. 在 config/config.yaml 的 backend.api.api_key 中填写\n"
                "获取地址：https://platform.deepseek.com/api_keys"
            )
        logger.info(
            "后端启动：DeepSeek API（model=%s, base_url=%s, api_key=%s）",
            self._model,
            self._base_url,
            _mask(self._api_key),
        )
        try:
            self._chat([{"role": "user", "content": "ping"}], timeout=min(self._timeout, 10.0))
            logger.info("API 连通性测试通过")
        except BackendError as exc:
            logger.warning("API 连通性测试失败（不阻塞启动）：%s", exc)

    def stop(self) -> None:
        return None

    def new_conversation(self) -> None:
        self._messages = []
        self._session_id = None
        logger.info("已开启新会话（messages 已清空）")

    def ask(
        self,
        text: str,
        *,
        timeout: float | None = None,
        label: str = "消息",
        approval_mgr: Any = None,
        prepend: str = "",
    ) -> str:
        actual = (prepend + "\n\n" + text) if prepend else text

        if self._cfg.approval.send_to_deepseek and approval_mgr is not None:
            result = approval_mgr.ask_send(actual, label=label)
            if not result.approved:
                raise BackendError("用户拒绝发送")
            actual = result.text

        self._throttle()
        self._messages.append({"role": "user", "content": actual})
        try:
            reply = self._chat(self._messages, timeout=timeout)
        except BackendError:
            self._messages.pop()
            raise
        self._messages.append({"role": "assistant", "content": reply})
        return reply

    def _throttle(self) -> None:
        if self._min_interval <= 0:
            return
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            wait = self._min_interval - elapsed
            logger.debug("限流等待 %.2fs", wait)
            time.sleep(wait)
        self._last_call = time.time()

    def _chat(self, messages: list[dict[str, str]], timeout: float | None = None) -> str:
        import requests

        url = self._base_url + "/chat/completions"
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": "Bearer " + self._api_key,
            "Content-Type": "application/json",
        }
        actual_timeout = timeout or self._timeout
        last_error: Exception | None = None

        for attempt in range(1, self._retry + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=actual_timeout)
                if resp.status_code >= 500:
                    raise BackendError("服务器错误 " + str(resp.status_code))
                if resp.status_code == 429:
                    raise BackendError("触发速率限制，请降低调用频率")
                if resp.status_code >= 400:
                    raise BackendError("API 错误 " + str(resp.status_code) + "：" + resp.text[:300])
                data = resp.json()
                choices = data.get("choices") or []
                if not choices:
                    raise BackendError("API 返回不含 choices：" + str(data)[:300])
                message = choices[0].get("message") or {}
                content = (message.get("content") or "").strip()
                if not content:
                    raise BackendError("API 返回空内容")
                self._session_id = data.get("id") or self._session_id
                return content
            except BackendError as exc:
                # 4xx / 限流类错误立即抛出，避免无谓重试。
                if "触发速率限制" in str(exc) or "API 错误 4" in str(exc):
                    raise
                last_error = exc
            except Exception as exc:
                last_error = exc

            backoff = min(2 ** (attempt - 1), 8)
            logger.warning(
                "API 调用失败（第 %d/%d 次）：%s，%.1fs 后重试",
                attempt,
                self._retry,
                last_error,
                backoff,
            )
            time.sleep(backoff)

        raise BackendError("API 调用重试 " + str(self._retry) + " 次后仍失败：" + str(last_error))
