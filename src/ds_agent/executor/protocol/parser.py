# ds-agent 协议提取与解析。
#
# 输入是 LLM 的文本回复，输出是 Task 或 None。
from __future__ import annotations

import json
import re
from typing import Any

from ds_agent.executor.protocol.schema import (
    ALLOWED_ON_ERROR,
    META_KEYS,
    REQUIRED_FIELDS,
    SUPPORTED_ACTIONS,
    Step,
    Task,
)
from ds_agent.logging_setup import get_logger

logger = get_logger(__name__)

_DS_AGENT_RE = re.compile(r"```ds-agent\s*\n(.*?)\n```", re.DOTALL)
_JSON_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL)


def extract_protocol(text: str) -> Task | None:
    # 从文本中提取协议。
    #
    # 优先 ds-agent 代码块，其次 json 代码块。从后往前找，
    # 取第一个能解析成合法 Task 的候选。
    if not text:
        return None

    candidates: list[str] = []
    for m in _DS_AGENT_RE.finditer(text):
        candidates.append(m.group(1).strip())
    for m in _JSON_RE.finditer(text):
        candidates.append(m.group(1).strip())

    for raw in reversed(candidates):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        task = _parse_protocol(data)
        if task:
            return task
    return None


def _parse_protocol(data: Any) -> Task | None:
    if not isinstance(data, dict):
        return None

    # 单步格式：{"action": "...", ...}
    if "action" in data and "task" not in data:
        step = _parse_step(data)
        if not step:
            return None
        return Task(name="单步操作", mode="single", steps=[step])

    task_data = data.get("task")
    if not isinstance(task_data, dict):
        return None

    steps_raw = task_data.get("steps")
    if not isinstance(steps_raw, list):
        return None
    # 允许空 steps：用于"无需执行"
    steps: list[Step] = []
    for raw in steps_raw:
        step = _parse_step(raw)
        if not step:
            return None
        steps.append(step)

    vars_raw = task_data.get("vars") or {}
    if not isinstance(vars_raw, dict):
        vars_raw = {}

    return Task(
        name=str(task_data.get("name", "未命名任务")),
        summary=str(task_data.get("summary", "")),
        vars=vars_raw,
        steps=steps,
        mode="task",
    )


def _parse_step(raw: Any) -> Step | None:
    if not isinstance(raw, dict):
        return None

    action = str(raw.get("action", "")).strip()
    if action not in SUPPORTED_ACTIONS:
        return None

    for field in REQUIRED_FIELDS[action]:
        if field not in raw:
            return None

    args = {k: v for k, v in raw.items() if k not in META_KEYS}

    on_error = str(raw.get("on_error", "stop")).strip().lower()
    if on_error not in ALLOWED_ON_ERROR:
        on_error = "stop"

    return Step(
        action=action,
        args=args,
        note=str(raw.get("note", "")),
        on_error=on_error,
    )
