# 工具注册表与 @tool 装饰器。
#
# 职责：
#   - 装饰器登记工具元信息（名称、说明、参数 schema、权限级别）
#   - dispatch 负责按名调用，统一错误封装
#   - discover 扫描本包下模块，触发注册
from __future__ import annotations

import importlib
import os
import pkgutil
from collections.abc import Callable
from typing import Any

from ds_agent.logging_setup import get_logger

logger = get_logger(__name__)

# 权限级别：L0 只读、L1 写入、L2 破坏性操作。
PERMISSION_LEVELS = ("L0", "L1", "L2")

_TOOLS: dict[str, dict[str, Any]] = {}


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    permission: str = "L0",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    # 把一个函数注册为工具。重复注册同名工具会抛错。
    if permission not in PERMISSION_LEVELS:
        raise ValueError("未知权限级别：" + str(permission))

    def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
        if name in _TOOLS:
            raise RuntimeError("工具重复注册：" + name)
        _TOOLS[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "permission": permission,
            "fn": fn,
        }
        return fn

    return deco


def get_schemas() -> list[dict[str, Any]]:
    # 返回 function calling 风格的 schema 列表。
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in _TOOLS.values()
    ]


def all_tools() -> list[dict[str, Any]]:
    return list(_TOOLS.values())


def get_tool(name: str) -> dict[str, Any]:
    return _TOOLS.get(name, {})


def dispatch(name: str, args: dict[str, Any]) -> dict[str, Any]:
    # 执行工具。异常被捕获并转换为 {"ok": False, "error": ...}。
    spec = _TOOLS.get(name)
    if not spec:
        return {"ok": False, "error": "未知工具：" + name}
    try:
        result = spec["fn"](**(args or {}))
    except TypeError as exc:
        return {"ok": False, "error": "参数错误：" + str(exc)}
    except Exception as exc:
        logger.exception("工具 %s 执行失败", name)
        return {"ok": False, "error": "执行失败：" + str(exc)}
    if isinstance(result, dict):
        return result
    return {"ok": True, "result": result}


def reset_registry() -> None:
    # 清空注册表。仅供测试使用。
    _TOOLS.clear()


def discover() -> None:
    # 扫描本包并 import 非下划线前缀的模块，触发 @tool 注册。
    here = os.path.dirname(os.path.abspath(__file__))
    for _, modname, _ in pkgutil.iter_modules([here]):
        if modname.startswith("_") or modname == "base":
            continue
        full = "ds_agent.tools." + modname
        try:
            importlib.import_module(full)
        except Exception:
            logger.exception("加载工具模块 %s 失败", full)
