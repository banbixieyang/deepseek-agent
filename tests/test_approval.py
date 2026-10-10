# 审批状态测试。
from __future__ import annotations

from ds_agent.core.approval import ApprovalManager, ApprovalResult


def test_approval_result_defaults():
    r = ApprovalResult(True)
    assert r.approved is True
    assert r.text == ""
    assert r.modified is False


def test_auto_write_skips_prompt(monkeypatch):
    mgr = ApprovalManager()
    mgr._auto_write = True
    assert mgr.ask_write("a.txt", "x", exists=False) is True
    assert mgr.auto_write is True


def test_reset_clears_state():
    mgr = ApprovalManager()
    mgr._auto_write = True
    mgr.note_backup("a.txt", "b.bak")
    mgr.reset()
    assert mgr.auto_write is False
    assert mgr.list_backups() == []


def test_ask_batch_returns_bool(monkeypatch):
    mgr = ApprovalManager()
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    assert mgr.ask_batch(10) is True


def test_ask_batch_auto(monkeypatch):
    mgr = ApprovalManager()
    monkeypatch.setattr("builtins.input", lambda *_: "a")
    assert mgr.ask_batch(10) is True
    assert mgr.auto_write is True
