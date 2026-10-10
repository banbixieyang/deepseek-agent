# BrainBackend 协议：任何后端都必须实现该接口。
#
# 上层（executor/loop.py）只依赖此协议，不关心具体实现。
# 通过 bridge.factory.create_backend(cfg) 获得实例。
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BrainBackend(Protocol):
    # "大脑"后端的统一接口。

    @property
    def kind(self) -> str:
        # 后端类型标识：api / web / openai / ollama。
        ...

    @property
    def session_id(self) -> str | None:
        # 当前会话 id，可能为 None。
        ...

    def start(self) -> None:
        # 启动后端（健康检查、加载凭据等）。
        ...

    def stop(self) -> None:
        # 停止后端，释放资源。
        ...

    def new_conversation(self) -> None:
        # 开启一个新会话，清空上下文。
        ...

    def ask(
        self,
        text: str,
        *,
        timeout: float | None = None,
        label: str = "消息",
        approval_mgr: Any = None,
        prepend: str = "",
    ) -> str:
        # 发送一条消息并返回回复文本。
        ...


class BackendError(RuntimeError):
    # 后端统一错误类型。
    pass


class RiskNotAcknowledgedError(BackendError):
    # 网页后端未确认风险时抛出。
    pass
