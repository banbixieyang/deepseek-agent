# Shell 工具。在工作区执行代码文件。
#
# runner 映射可通过配置扩展（当前内置 .py / .js / .sh）。
from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from ds_agent.config import get_config, resolve_path
from ds_agent.tools._common import resolve_in_workspace
from ds_agent.tools.base import tool

_MAX_TIMEOUT = 120


def _runners() -> dict[str, list[str]]:
    # 返回扩展名到命令前缀的映射。
    return {
        ".py": [sys.executable],
        ".js": ["node"],
        ".sh": ["bash"],
    }


@tool(
    name="run_code",
    description=(
        "运行工作区里的代码文件，返回 stdout / stderr / 退出码。支持 .py / .js / .sh 文件。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径（相对工作区）"},
            "timeout": {"type": "integer", "description": "超时秒数，默认 30"},
        },
        "required": ["path"],
    },
    permission="L1",
)
def run_code(path: str, timeout: int = 30) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path, must_exist=True)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    if not os.path.isfile(abs_path):
        return {"ok": False, "error": "文件不存在：" + path}

    ext = os.path.splitext(abs_path)[1].lower()
    prefix = _runners().get(ext)
    if not prefix:
        return {"ok": False, "error": "不支持的文件类型：" + ext}

    cmd = prefix + [abs_path]
    timeout = max(1, min(int(timeout), _MAX_TIMEOUT))
    cfg = get_config()
    cwd = str(resolve_path(cfg.paths.workspace_dir))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "运行超时（" + str(timeout) + "s）"}
    except FileNotFoundError as exc:
        return {"ok": False, "error": "找不到解释器：" + str(exc)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[-4000:],
        "stderr": (result.stderr or "")[-4000:],
    }
