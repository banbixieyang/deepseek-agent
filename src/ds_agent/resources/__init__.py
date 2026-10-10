# resources 包：只读资源（协议规范、提示词、示例）。
#
# 通过 importlib.resources 访问，保证打包后可读。
from __future__ import annotations

from importlib import resources as _resources

_PACKAGE = "ds_agent.resources"


def read_bytes(relative_path: str) -> bytes:
    # 读取资源文件原始字节。
    return _resources.files(_PACKAGE).joinpath(relative_path).read_bytes()


def load_text(relative_path: str) -> str:
    # 读取资源文本（UTF-8）。
    return read_bytes(relative_path).decode("utf-8")


def list_files(relative_dir: str = "") -> list[str]:
    # 列出某个子目录下的文件（非递归）。
    base = _resources.files(_PACKAGE)
    if relative_dir:
        base = base.joinpath(relative_dir)
    return sorted(entry.name for entry in base.iterdir() if entry.is_file())


__all__ = ["list_files", "load_text", "read_bytes"]
