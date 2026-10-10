# 完成信号判定测试。
from __future__ import annotations

from ds_agent.executor.finish import looks_like_finish


def test_finish_marker_in_tail():
    text = "以上步骤已完成。任务完成，等待你的下一步指令。"
    assert looks_like_finish(text) is True


def test_protocol_block_is_not_finish():
    text = "接下来执行：\n```ds-agent\n{...}\n```"
    assert looks_like_finish(text) is False


def test_action_hint_in_head_is_not_finish():
    text = "我需要写入文件并运行测试。" + "补充说明" * 100
    assert looks_like_finish(text) is False


def test_short_text_treated_as_finish():
    assert looks_like_finish("好的。") is True


def test_empty_is_finish():
    assert looks_like_finish("") is True
