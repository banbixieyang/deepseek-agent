# 协议解析测试。
from __future__ import annotations

from ds_agent.executor.protocol import extract_protocol


def test_extract_ds_agent_block():
    text = """说明文字

```ds-agent
{
  "protocol": "ds-agent/1.0",
  "mode": "task",
  "task": {
    "name": "demo",
    "steps": [
      {"action": "write_file", "path": "a.txt", "content": "hi"}
    ]
  }
}
```
"""
    task = extract_protocol(text)
    assert task is not None
    assert task.name == "demo"
    assert len(task.steps) == 1
    assert task.steps[0].action == "write_file"


def test_extract_single_step_format():
    text = """```json
{"action": "mkdir", "path": "src"}
```"""
    task = extract_protocol(text)
    assert task is not None
    assert task.mode == "single"
    assert task.steps[0].action == "mkdir"


def test_extract_returns_none_on_bad_json():
    assert extract_protocol("```ds-agent\nnot json\n```") is None


def test_extract_returns_none_on_unknown_action():
    text = """```ds-agent
{"protocol": "ds-agent/1.0", "task": {"name": "x",
  "steps": [{"action": "frobnicate", "path": "a"}]}}
```"""
    assert extract_protocol(text) is None


def test_empty_steps_is_valid():
    text = """```ds-agent
{"protocol": "ds-agent/1.0", "task": {"name": "无需执行", "steps": []}}
```"""
    task = extract_protocol(text)
    assert task is not None
    assert task.steps == []


def test_picks_last_valid_candidate():
    text = """```json
{"action": "mkdir", "path": "a"}
```

```ds-agent
{"protocol": "ds-agent/1.0", "task": {"name": "第二",
  "steps": [{"action": "mkdir", "path": "b"}]}}
```"""
    task = extract_protocol(text)
    assert task is not None
    assert task.name == "第二"
