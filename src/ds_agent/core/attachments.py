# 附件：把本地文件或文件夹整理成可发送给 DeepSeek 的文本。
#
# 合并原版的 file_attach 与 folder_attach，共享跳过规则、路径解析与截断逻辑。
from __future__ import annotations

import os

from ds_agent.config import get_config, resolve_path
from ds_agent.logging_setup import get_logger

logger = get_logger(__name__)


def _workspace() -> str:
    return str(resolve_path(get_config().paths.workspace_dir))


def _resolve_target(raw: str) -> str | None:
    # 把用户输入解析为存在的绝对路径。
    # 优先按工作区相对路径解析，其次按原路径解析。
    if not raw:
        return None
    clean = raw.strip().strip('"').strip("'")
    if not clean:
        return None

    if os.path.isabs(clean):
        candidate = os.path.abspath(clean)
        return candidate if os.path.exists(candidate) else None

    workspace = _workspace()
    candidate = os.path.abspath(os.path.join(workspace, clean))
    if os.path.exists(candidate):
        return candidate
    candidate = os.path.abspath(clean)
    return candidate if os.path.exists(candidate) else None


def _rel_to_workspace(abs_path: str) -> tuple[str, bool]:
    # 返回 (相对路径, 是否在工作区内)。
    workspace = _workspace()
    if abs_path == workspace or abs_path.startswith(workspace + os.sep):
        rel = os.path.relpath(abs_path, workspace)
        if rel == ".":
            return "", True
        return rel.replace(os.sep, "/"), True
    return "", False


def _should_skip_dir(name: str, extra: list[str]) -> bool:
    if name in extra:
        return True
    if name.startswith(".") and name not in (".", ".."):
        return True
    return False


def _should_skip_file(name: str, extra_exts: list[str]) -> bool:
    if name in (".DS_Store", "Thumbs.db"):
        return True
    ext = os.path.splitext(name)[1].lower()
    return ext in extra_exts


# ---------- 单文件 ----------


def attach_file(path: str, max_chars: int | None = None) -> str | None:
    # 读取单个文件，返回格式化文本；失败返回 None。
    cfg = get_config()
    limit = int(max_chars or cfg.attach.max_file_chars)

    abs_path = _resolve_target(path)
    if not abs_path or not os.path.isfile(abs_path):
        print("      文件不存在：" + str(path))
        return None

    try:
        size = os.path.getsize(abs_path)
        with open(abs_path, encoding="utf-8", errors="replace") as f:
            content = f.read(limit)
    except Exception as exc:
        print("      读取失败：" + str(exc))
        return None

    truncated = size > limit
    basename = os.path.basename(abs_path)
    rel, in_ws = _rel_to_workspace(abs_path)

    header = "[附加文件：" + basename
    if in_ws:
        header += " | 工作区相对路径：" + rel
    else:
        header += " | 位置：工作区外（只能读取，不能直接写入）"
    header += " | 大小 " + str(size) + " 字节"
    if truncated:
        header += " | 已截断至 " + str(limit) + " 字符"
    header += "]\n"

    print(
        "      已读取 "
        + basename
        + "（"
        + str(len(content))
        + " 字符"
        + ("，已截断" if truncated else "")
        + "）"
    )
    return header + content


# ---------- 文件夹 ----------


def _build_tree(
    abs_dir: str,
    rel_dir: str,
    skip_dirs: list[str],
    skip_exts: list[str],
    prefix: str = "",
) -> tuple[list[str], list[tuple[str, str, int]]]:
    # 递归遍历目录，返回 (目录树行, 文件列表)。
    lines: list[str] = []
    files: list[tuple[str, str, int]] = []

    try:
        entries = sorted(os.listdir(abs_dir))
    except Exception as exc:
        logger.debug("列目录失败 %s：%s", abs_dir, exc)
        return lines, files

    dirs: list[str] = []
    plain: list[str] = []
    for name in entries:
        full = os.path.join(abs_dir, name)
        if os.path.isdir(full):
            if not _should_skip_dir(name, skip_dirs):
                dirs.append(name)
        else:
            if not _should_skip_file(name, skip_exts):
                plain.append(name)

    items: list[tuple[str, bool]] = [(d, True) for d in dirs] + [(f, False) for f in plain]
    for i, (name, is_dir) in enumerate(items):
        last = i == len(items) - 1
        marker = "└── " if last else "├── "
        lines.append(prefix + marker + name + ("/" if is_dir else ""))

        full = os.path.join(abs_dir, name)
        if is_dir:
            next_rel = os.path.join(rel_dir, name) if rel_dir else name
            ext = "    " if last else "│   "
            sub_lines, sub_files = _build_tree(full, next_rel, skip_dirs, skip_exts, prefix + ext)
            lines.extend(sub_lines)
            files.extend(sub_files)
        else:
            try:
                size = os.path.getsize(full)
            except Exception:
                size = 0
            rel_path = os.path.join(rel_dir, name) if rel_dir else name
            files.append((rel_path, full, size))

    return lines, files


def attach_folder(path: str) -> str | None:
    # 读取整个文件夹，返回格式化文本；失败返回 None。
    cfg = get_config()
    max_files = int(cfg.attach.max_folder_files)
    max_total = int(cfg.attach.max_folder_total_chars)
    max_per_file = int(cfg.attach.max_per_file_chars)
    skip_dirs = list(cfg.attach.skip_dirs)
    skip_exts = list(cfg.attach.skip_exts)

    abs_path = _resolve_target(path)
    if not abs_path or not os.path.isdir(abs_path):
        print("      文件夹不存在：" + str(path))
        return None

    basename = os.path.basename(abs_path) or abs_path
    rel_root, in_ws = _rel_to_workspace(abs_path)

    print("      扫描文件夹 " + basename + " ...")
    tree_lines, all_files = _build_tree(abs_path, "", skip_dirs, skip_exts)
    if not all_files:
        print("      文件夹为空或全是跳过的文件")
        return None

    truncated_files = False
    if len(all_files) > max_files:
        all_files = all_files[:max_files]
        truncated_files = True

    blocks: list[str] = []
    total_chars = 0
    included = 0
    for rel_path, full_path, size in all_files:
        if total_chars >= max_total:
            break
        try:
            with open(full_path, encoding="utf-8", errors="replace") as f:
                content = f.read(max_per_file)
        except Exception:
            continue

        truncated = size > max_per_file
        rel_display = rel_path.replace(os.sep, "/")
        block = "--- " + rel_display + " (" + str(size) + " 字节"
        if truncated:
            block += "，已截断"
        block += ") ---\n"
        block += content
        if not content.endswith("\n"):
            block += "\n"
        blocks.append(block)
        total_chars += len(content)
        included += 1

    header = "[附加文件夹：" + basename
    if in_ws:
        header += " | 工作区相对路径：" + (rel_root or "(根目录)")
    else:
        header += " | 位置：工作区外（只能读取，不能直接写入）"
    header += " | 共 " + str(included) + " 个文件"
    if truncated_files:
        header += "（超过上限，已截断）"
    header += "]\n"

    parts: list[str] = [header]
    parts.append("\n=== 目录结构 ===\n")
    if in_ws and rel_root:
        parts.append(rel_root + "/\n")
    for line in tree_lines:
        parts.append(line + "\n")
    parts.append("\n=== 文件内容 ===\n\n")
    parts.append("\n".join(blocks))

    result = "".join(parts)
    print("      已读取 " + str(included) + " 个文件（" + str(len(result)) + " 字符）")
    return result


# ---------- 自动分流 ----------


def attach_path(path: str) -> str | None:
    # 按路径类型自动选择 attach_file 或 attach_folder。
    abs_path = _resolve_target(path)
    if not abs_path:
        print("      路径不存在：" + str(path))
        return None
    if os.path.isdir(abs_path):
        print("      [识别为文件夹，导入整个目录]")
        return attach_folder(path)
    print("      [识别为单个文件]")
    return attach_file(path)
