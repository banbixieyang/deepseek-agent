# 任务执行器。按步骤顺序执行，收集每步结果。
#
# 写入类操作是否审批由 cfg.approval.tools 决定，不再硬编码。
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from ds_agent.config import get_config, resolve_path
from ds_agent.executor.protocol.schema import Step, Task
from ds_agent.logging_setup import get_logger
from ds_agent.tools.base import dispatch

logger = get_logger(__name__)


@dataclass
class StepResult:
    # 单个步骤的执行结果。
    step: Step
    ok: bool
    detail: str = ""
    error: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class TaskRunner:
    # 顺序执行 Task 的 steps。

    def __init__(self, approval_mgr: Any = None) -> None:
        self.approval = approval_mgr

    def run(self, task: Task) -> list[StepResult]:
        # 执行整个任务，返回每步的结果。
        results: list[StepResult] = []
        total = len(task.steps)
        cfg = get_config()
        approve_tools = set(cfg.approval.tools)

        for i, step in enumerate(task.steps, 1):
            path_str = str(step.args.get("path", ""))
            print("\n   [" + str(i) + "/" + str(total) + "] " + step.action + " " + path_str)
            if step.note:
                print("         备注：" + step.note)

            # 需要审批的操作
            if cfg.approval.write_file and self.approval and step.action in approve_tools:
                if not self._approve_step(step):
                    sr = StepResult(step=step, ok=False, error="用户拒绝")
                    results.append(sr)
                    print("         用户拒绝")
                    if step.on_error == "stop":
                        break
                    continue

            result = dispatch(step.action, step.args)
            sr = StepResult(
                step=step,
                ok=bool(result.get("ok", False)),
                detail=str(result.get("note", "")),
                error=str(result.get("error", "")),
                raw=result if isinstance(result, dict) else {},
            )
            results.append(sr)

            if sr.ok:
                print("         完成：" + (sr.detail or "ok"))
            else:
                print("         失败：" + sr.error)
                if step.on_error == "stop":
                    print("         停止后续执行")
                    break

        return results

    def _approve_step(self, step: Step) -> bool:
        # 对单个写入类步骤做审批。
        if self.approval is None:
            return True

        path = str(step.args.get("path", ""))
        if step.action in ("write_file", "append_file"):
            content = str(step.args.get("content", ""))
        elif step.action == "edit_file":
            content = (
                "--- 原文 ---\n"
                + str(step.args.get("old_text", ""))
                + "\n--- 新文 ---\n"
                + str(step.args.get("new_text", ""))
            )
        elif step.action == "delete_file":
            content = "（删除此文件）"
        elif step.action in ("move_file", "copy_file"):
            content = "-> " + str(step.args.get("to", ""))
        else:
            content = ""

        abs_path = self._resolve_for_preview(path)
        exists = bool(abs_path) and os.path.isfile(abs_path)
        return self.approval.ask_write(path=path, content=content, exists=exists)

    @staticmethod
    def _resolve_for_preview(path: str) -> str | None:
        # 预览用路径解析，越界返回 None。
        if not path:
            return None
        cfg = get_config()
        workspace = str(resolve_path(cfg.paths.workspace_dir))
        if os.path.isabs(path):
            abs_path = os.path.abspath(path)
        else:
            abs_path = os.path.abspath(os.path.join(workspace, path))
        if abs_path != workspace and not abs_path.startswith(workspace + os.sep):
            return None
        return abs_path
