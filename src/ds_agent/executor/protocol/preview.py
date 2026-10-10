# 预览渲染：把 Task 渲染成人类可读的文本与目录树。
from __future__ import annotations

from collections.abc import Iterable

from ds_agent.executor.protocol.schema import Task


def render_tree(paths: Iterable[str]) -> list[str]:
    # 把一组路径渲染成树状文本行。
    tree: dict[str, dict] = {}
    for p in paths:
        if not p:
            continue
        parts = str(p).replace("\\", "/").split("/")
        cur = tree
        for part in parts:
            if part == "":
                continue
            cur = cur.setdefault(part, {})

    lines: list[str] = []

    def walk(node: dict[str, dict], prefix: str) -> None:
        items = sorted(node.items())
        for i, (name, children) in enumerate(items):
            last = i == len(items) - 1
            marker = "└── " if last else "├── "
            lines.append(prefix + marker + name)
            if children:
                walk(children, prefix + ("    " if last else "│   "))

    walk(tree, "")
    return lines


def render_preview(task: Task) -> str:
    # 生成可读预览，供审批前展示。
    lines: list[str] = []
    lines.append("任务：" + task.name)
    if task.summary:
        lines.append("   " + task.summary)
    lines.append("   模式：" + task.mode)
    lines.append("   步骤：" + str(len(task.steps)) + " 步")
    lines.append("")

    creates: list[str] = []
    modifies: list[str] = []
    deletes: list[str] = []
    moves: list[str] = []
    runs: list[str] = []
    reads: list[str] = []
    all_paths: set[str] = set()

    for step in task.steps:
        action = step.action
        p = str(step.args.get("path", ""))
        to = str(step.args.get("to", ""))
        if p:
            all_paths.add(p)
        if to:
            all_paths.add(to)

        if action == "write_file":
            creates.append(p)
        elif action in ("edit_file", "append_file"):
            modifies.append(p)
        elif action == "delete_file":
            deletes.append(p)
        elif action in ("move_file", "copy_file"):
            moves.append(p + " → " + to)
        elif action == "run_code":
            runs.append(p)
        elif action == "read_file":
            reads.append(p)

    if all_paths:
        lines.append("涉及的文件结构：")
        for line in render_tree(sorted(all_paths)):
            lines.append("   " + line)
        lines.append("")

    def _block(title: str, items: list[str]) -> None:
        if not items:
            return
        lines.append(title + "（" + str(len(items)) + " 个）：")
        for item in items:
            lines.append("     " + item)
        lines.append("")

    _block("写入文件", creates)
    _block("修改文件", modifies)
    _block("删除文件", deletes)
    _block("移动/复制", moves)
    _block("运行代码", runs)
    _block("读取文件", reads)

    return "\n".join(lines).rstrip()
