# 执行结果反馈格式化。
#
# 把 TaskRunner 的 StepResult 列表汇总成发给后端的纯文本。
from __future__ import annotations

from ds_agent.executor.protocol.schema import Task
from ds_agent.executor.runner import StepResult

_MAX_STDOUT_LINES = 50
_MAX_STDERR_LINES = 30
_MAX_READ_LINES = 100


def format_results(task: Task, results: list[StepResult]) -> str:
    # 生成 [执行结果] 文本块。
    lines: list[str] = ["[执行结果]"]
    lines.append("任务：" + task.name)
    lines.append("总步数：" + str(len(results)))
    ok_count = sum(1 for r in results if r.ok)
    lines.append("成功：" + str(ok_count) + "/" + str(len(results)))
    lines.append("")

    for i, r in enumerate(results, 1):
        step = r.step
        path = str(step.args.get("path", ""))
        mark = "[OK]" if r.ok else "[FAIL]"
        lines.append(mark + " [" + str(i) + "] " + step.action + " " + path)

        if r.detail:
            lines.append("   " + r.detail)
        if r.error:
            lines.append("   错误：" + r.error)

        if step.action == "run_code" and isinstance(r.raw, dict):
            rc = r.raw.get("returncode", "?")
            out = r.raw.get("stdout", "") or ""
            err = r.raw.get("stderr", "") or ""
            lines.append("   退出码：" + str(rc))
            if out:
                lines.append("   stdout:")
                for line in out.split("\n")[:_MAX_STDOUT_LINES]:
                    lines.append("     " + line)
            if err:
                lines.append("   stderr:")
                for line in err.split("\n")[:_MAX_STDERR_LINES]:
                    lines.append("     " + line)

        if step.action == "read_file" and isinstance(r.raw, dict) and r.raw.get("ok"):
            content = r.raw.get("content", "") or ""
            lines.append("   内容：")
            for line in content.split("\n")[:_MAX_READ_LINES]:
                lines.append("     " + line)

    return "\n".join(lines)
