# 文件工具。所有操作限制在工作区内，写操作前自动备份。
from __future__ import annotations

import os
import shutil
from typing import Any

from ds_agent.tools._common import ensure_parent, make_backup, resolve_in_workspace
from ds_agent.tools.base import tool


def _ok(note: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": True, "note": note}
    payload.update(extra)
    return payload


def _fail(error: str) -> dict[str, Any]:
    return {"ok": False, "error": error}


@tool(
    name="mkdir",
    description="创建目录（含所有父目录）。已存在不报错。",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "目录路径"}},
        "required": ["path"],
    },
    permission="L1",
)
def mkdir(path: str) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path)
        os.makedirs(abs_path, exist_ok=True)
    except ValueError as exc:
        return _fail(str(exc))
    return _ok("已创建目录 " + path, path=abs_path)


@tool(
    name="write_file",
    description=(
        "把内容写入工作区文件。path 相对工作区。"
        "content 必须是完整内容，不要省略。写入前会自动备份已有文件。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径（相对工作区）"},
            "content": {"type": "string", "description": "完整文件内容"},
        },
        "required": ["path", "content"],
    },
    permission="L1",
)
def write_file(path: str, content: str) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path)
    except ValueError as exc:
        return _fail(str(exc))

    ensure_parent(abs_path)
    backup = make_backup(abs_path) if os.path.isfile(abs_path) else ""

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content)

    note = "已保存到 " + os.path.basename(abs_path) + "（" + str(len(content)) + " 字符）"
    if backup:
        note += "（旧版本已备份）"
    return _ok(note, path=abs_path, size=len(content), backup=backup)


@tool(
    name="edit_file",
    description=(
        "对已有文件做局部替换。old_text 必须在文件中唯一出现。比 write_file 更安全，只改指定部分。"
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径（相对工作区）"},
            "old_text": {"type": "string", "description": "要被替换的原文（必须唯一）"},
            "new_text": {"type": "string", "description": "替换成的新内容"},
        },
        "required": ["path", "old_text", "new_text"],
    },
    permission="L1",
)
def edit_file(path: str, old_text: str, new_text: str) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path, must_exist=True)
    except ValueError as exc:
        return _fail(str(exc))
    if not os.path.isfile(abs_path):
        return _fail("文件不存在：" + path)

    with open(abs_path, encoding="utf-8") as f:
        content = f.read()

    count = content.count(old_text)
    if count == 0:
        return _fail("在 " + path + " 里找不到 old_text")
    if count > 1:
        return _fail(
            "old_text 在 " + path + " 里出现 " + str(count) + " 次，不唯一。请扩大上下文。"
        )

    backup = make_backup(abs_path)
    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(content.replace(old_text, new_text, 1))

    note = "已修改 " + os.path.basename(abs_path) + "（替换 1 处）"
    if backup:
        note += "（旧版本已备份）"
    return _ok(note, path=abs_path, backup=backup)


@tool(
    name="append_file",
    description="把内容追加到文件末尾。文件不存在时新建。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
    permission="L1",
)
def append_file(path: str, content: str) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path)
    except ValueError as exc:
        return _fail(str(exc))

    ensure_parent(abs_path)
    backup = make_backup(abs_path) if os.path.isfile(abs_path) else ""

    with open(abs_path, "a", encoding="utf-8") as f:
        f.write(content)

    return _ok(
        "已追加到 " + os.path.basename(abs_path),
        path=abs_path,
        size=len(content),
        backup=backup,
    )


@tool(
    name="delete_file",
    description="删除工作区文件（会先备份）。",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
    permission="L2",
)
def delete_file(path: str) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path, must_exist=True)
    except ValueError as exc:
        return _fail(str(exc))
    if not os.path.isfile(abs_path):
        return _fail("文件不存在：" + path)

    backup = make_backup(abs_path)
    os.remove(abs_path)
    return _ok("已删除 " + os.path.basename(abs_path) + "（已备份）", path=abs_path, backup=backup)


@tool(
    name="move_file",
    description="移动或重命名文件。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "源路径"},
            "to": {"type": "string", "description": "目标路径"},
        },
        "required": ["path", "to"],
    },
    permission="L2",
)
def move_file(path: str, to: str) -> dict[str, Any]:
    try:
        src = resolve_in_workspace(path, must_exist=True)
        dst = resolve_in_workspace(to)
    except ValueError as exc:
        return _fail(str(exc))
    if not os.path.isfile(src):
        return _fail("源文件不存在：" + path)
    if os.path.exists(dst):
        return _fail("目标已存在：" + to)

    ensure_parent(dst)
    backup = make_backup(src)
    shutil.move(src, dst)
    return _ok("已移动 " + path + " → " + to, path=dst, backup=backup)


@tool(
    name="copy_file",
    description="复制文件。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "to": {"type": "string"},
        },
        "required": ["path", "to"],
    },
    permission="L1",
)
def copy_file(path: str, to: str) -> dict[str, Any]:
    try:
        src = resolve_in_workspace(path, must_exist=True)
        dst = resolve_in_workspace(to)
    except ValueError as exc:
        return _fail(str(exc))
    if not os.path.isfile(src):
        return _fail("源文件不存在：" + path)

    ensure_parent(dst)
    shutil.copy2(src, dst)
    return _ok("已复制 " + path + " → " + to, path=dst)


@tool(
    name="read_file",
    description="读取工作区文件内容。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "max_chars": {"type": "integer", "description": "最多读取字符数，默认 50000"},
        },
        "required": ["path"],
    },
    permission="L0",
)
def read_file(path: str, max_chars: int = 50000) -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path, must_exist=True)
    except ValueError as exc:
        return _fail(str(exc))
    if not os.path.isfile(abs_path):
        return _fail("文件不存在：" + path)

    with open(abs_path, encoding="utf-8", errors="replace") as f:
        content = f.read(max_chars)
    return {
        "ok": True,
        "path": abs_path,
        "content": content,
        "size": os.path.getsize(abs_path),
    }


@tool(
    name="list_dir",
    description="列出工作区目录下的文件。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径，默认 '.'（工作区根）"},
        },
        "required": [],
    },
    permission="L0",
)
def list_dir(path: str = ".") -> dict[str, Any]:
    try:
        abs_path = resolve_in_workspace(path, must_exist=True)
    except ValueError as exc:
        return _fail(str(exc))
    if not os.path.isdir(abs_path):
        return _fail("目录不存在：" + path)

    items: list[dict[str, Any]] = []
    for name in sorted(os.listdir(abs_path)):
        full = os.path.join(abs_path, name)
        items.append(
            {
                "name": name,
                "type": "dir" if os.path.isdir(full) else "file",
                "size": os.path.getsize(full) if os.path.isfile(full) else 0,
            }
        )
    return {"ok": True, "path": abs_path, "items": items}
