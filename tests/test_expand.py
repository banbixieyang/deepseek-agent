# 变量展开测试。
from __future__ import annotations

from ds_agent.executor.protocol import (
    Step,
    Task,
    expand_task,
    expand_vars,
)


def test_expand_vars_string():
    assert expand_vars("hello {{NAME}}", {"NAME": "world"}) == "hello world"


def test_expand_vars_unknown_kept():
    assert expand_vars("{{NOPE}}", {}) == "{{NOPE}}"


def test_expand_vars_nested():
    data = {"a": ["{{X}}", {"b": "{{X}}!"}]}
    result = expand_vars(data, {"X": "y"})
    assert result == {"a": ["y", {"b": "y!"}]}


def test_expand_task_no_vars_returns_same():
    task = Task(name="t", steps=[Step("mkdir", {"path": "{{A}}"})])
    assert expand_task(task) is task


def test_expand_task_replaces_in_args():
    task = Task(
        name="{{P}}",
        vars={"P": "proj"},
        steps=[Step("write_file", {"path": "{{P}}/a.py", "content": "# {{P}}"})],
    )
    out = expand_task(task)
    assert out.name == "proj"
    assert out.steps[0].args["path"] == "proj/a.py"
    assert out.steps[0].args["content"] == "# proj"
