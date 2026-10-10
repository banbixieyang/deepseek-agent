# 文件工具测试：工作区隔离 + 备份。
from __future__ import annotations

import os
from pathlib import Path

from ds_agent.tools.base import dispatch


def test_write_and_read_roundtrip(isolated_config):
    r1 = dispatch("write_file", {"path": "a.txt", "content": "hello"})
    assert r1["ok"] is True

    r2 = dispatch("read_file", {"path": "a.txt"})
    assert r2["ok"] is True
    assert r2["content"] == "hello"


def test_backup_created_on_overwrite(isolated_config):
    dispatch("write_file", {"path": "a.txt", "content": "v1"})
    r = dispatch("write_file", {"path": "a.txt", "content": "v2"})
    assert r["ok"] is True
    assert r.get("backup")
    assert Path(r["backup"]).is_file()


def test_path_escape_rejected(isolated_config, tmp_path):
    outside = tmp_path / "outside.txt"
    r = dispatch("write_file", {"path": str(outside), "content": "nope"})
    assert r["ok"] is False
    assert "越界" in r["error"]


def test_delete_file(isolated_config):
    dispatch("write_file", {"path": "gone.txt", "content": "x"})
    r = dispatch("delete_file", {"path": "gone.txt"})
    assert r["ok"] is True
    assert not os.path.exists(os.path.join(isolated_config.paths.workspace_dir, "gone.txt"))


def test_edit_file_requires_unique_old_text(isolated_config):
    dispatch("write_file", {"path": "a.txt", "content": "aaa"})
    r = dispatch("edit_file", {"path": "a.txt", "old_text": "a", "new_text": "b"})
    assert r["ok"] is False
    assert "不唯一" in r["error"]


def test_edit_file_happy_path(isolated_config):
    dispatch("write_file", {"path": "a.txt", "content": "hello world"})
    r = dispatch("edit_file", {"path": "a.txt", "old_text": "world", "new_text": "ds-agent"})
    assert r["ok"] is True
    content = dispatch("read_file", {"path": "a.txt"})["content"]
    assert content == "hello ds-agent"


def test_list_dir(isolated_config):
    dispatch("write_file", {"path": "a.txt", "content": "x"})
    dispatch("mkdir", {"path": "sub"})
    r = dispatch("list_dir", {"path": "."})
    assert r["ok"] is True
    names = {item["name"] for item in r["items"]}
    assert "a.txt" in names
    assert "sub" in names
