# ds-agent 协议的数据结构与常量。
#
# SUPPORTED_ACTIONS 与 REQUIRED_FIELDS 是协议的单一事实来源。
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SUPPORTED_ACTIONS = {
    "mkdir",
    "write_file",
    "edit_file",
    "append_file",
    "delete_file",
    "move_file",
    "copy_file",
    "run_code",
    "read_file",
    "list_dir",
}

REQUIRED_FIELDS: dict[str, list[str]] = {
    "mkdir": ["path"],
    "write_file": ["path", "content"],
    "edit_file": ["path", "old_text", "new_text"],
    "append_file": ["path", "content"],
    "delete_file": ["path"],
    "move_file": ["path", "to"],
    "copy_file": ["path", "to"],
    "run_code": ["path"],
    "read_file": ["path"],
    "list_dir": [],
}

ALLOWED_ON_ERROR = ("stop", "continue")

META_KEYS = ("action", "note", "on_error", "id")


@dataclass
class Step:
    action: str
    args: dict[str, Any]
    note: str = ""
    on_error: str = "stop"

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, **self.args}


@dataclass
class Task:
    name: str
    summary: str = ""
    vars: dict[str, Any] = field(default_factory=dict)
    steps: list[Step] = field(default_factory=list)
    mode: str = "task"
