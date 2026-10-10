# 预览渲染测试。
from __future__ import annotations

from ds_agent.executor.protocol import Step, Task, render_preview, render_tree


def test_render_tree_basic():
    lines = render_tree(["src/a.py", "src/b.py", "README.md"])
    joined = "\n".join(lines)
    assert "src" in joined
    assert "a.py" in joined
    assert "README.md" in joined


def test_render_preview_contains_sections():
    task = Task(
        name="演示",
        summary="一句话",
        steps=[
            Step("write_file", {"path": "a.py", "content": "x"}),
            Step("run_code", {"path": "a.py"}),
        ],
    )
    out = render_preview(task)
    assert "演示" in out
    assert "一句话" in out
    assert "写入文件" in out
    assert "运行代码" in out


def test_render_preview_empty_task():
    task = Task(name="空任务")
    out = render_preview(task)
    assert "空任务" in out
    assert "步骤：0 步" in out
