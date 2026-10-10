# 文件工具的公共逻辑：路径解析、越界检查、备份。
from __future__ import annotations

import os
import shutil
import time

from ds_agent.config import get_config, resolve_path
from ds_agent.logging_setup import get_logger

logger = get_logger(__name__)


def workspace_dir() -> str:
    # 返回工作区绝对路径。
    cfg = get_config()
    return str(resolve_path(cfg.paths.workspace_dir))


def backup_dir() -> str:
    # 返回备份根目录绝对路径。
    cfg = get_config()
    return str(resolve_path(cfg.paths.backup_dir))


def resolve_in_workspace(path: str, must_exist: bool = False) -> str:
    # 把 path 解析为工作区内的绝对路径。
    #
    # 越界访问会被拒绝，抛出 ValueError。
    # must_exist=True 时，路径不存在也抛 ValueError。
    if not path:
        raise ValueError("路径为空")

    workspace = workspace_dir()
    if os.path.isabs(path):
        abs_path = os.path.abspath(path)
    else:
        abs_path = os.path.abspath(os.path.join(workspace, path))

    # 越界检查：必须在工作区内。
    if abs_path != workspace and not abs_path.startswith(workspace + os.sep):
        raise ValueError("路径越界，拒绝访问工作区之外的位置：" + path)

    if must_exist and not os.path.exists(abs_path):
        raise ValueError("路径不存在：" + path)

    return abs_path


def make_backup(abs_path: str) -> str:
    # 为已存在的文件创建备份。
    #
    # 备份结构：<backup_dir>/<文件名>/<时间戳>.bak
    # 文件不存在或未开启备份时返回空串。
    cfg = get_config()
    if not cfg.approval.write_file:
        # 未开启写入审批时仍然备份，避免误操作导致不可恢复。
        pass

    if not os.path.isfile(abs_path):
        return ""

    try:
        base = os.path.basename(abs_path)
        target_dir = os.path.join(backup_dir(), base)
        os.makedirs(target_dir, exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        ms = int((time.time() % 1) * 1000)
        target = os.path.join(target_dir, ts + "_" + str(ms).zfill(3) + ".bak")
        shutil.copy2(abs_path, target)
        return target
    except Exception as exc:
        logger.warning("备份失败：%s", exc)
        return ""


def ensure_parent(abs_path: str) -> None:
    # 确保目标文件的父目录存在。
    parent = os.path.dirname(abs_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
