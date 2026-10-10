# 模板变量展开：{{KEY}} -> 值。
from __future__ import annotations

import re
from typing import Any

from ds_agent.executor.protocol.schema import Step, Task

_VAR_RE = re.compile(r"\{\{(\w+)\}\}")


def expand_vars(value: Any, vars_dict: dict[str, Any]) -> Any:
    # 递归展开字符串、字典、列表里的 {{KEY}}。
    if isinstance(value, str):

        def repl(m: re.Match[str]) -> str:
            key = m.group(1)
            return str(vars_dict.get(key, m.group(0)))

        return _VAR_RE.sub(repl, value)
    if isinstance(value, dict):
        return {k: expand_vars(v, vars_dict) for k, v in value.items()}
    if isinstance(value, list):
        return [expand_vars(v, vars_dict) for v in value]
    return value


def expand_task(task: Task) -> Task:
    # 对任务名、摘要与所有步骤参数做变量展开，返回新 Task。
    if not task.vars:
        return task

    new_steps: list[Step] = []
    for step in task.steps:
        new_steps.append(
            Step(
                action=step.action,
                args=expand_vars(step.args, task.vars),
                note=expand_vars(step.note, task.vars),
                on_error=step.on_error,
            )
        )

    return Task(
        name=expand_vars(task.name, task.vars),
        summary=expand_vars(task.summary, task.vars),
        vars=dict(task.vars),
        steps=new_steps,
        mode=task.mode,
    )
