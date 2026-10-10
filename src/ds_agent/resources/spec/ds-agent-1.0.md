# ds-agent 协议 v1.0

## 顶层结构

```json
{
  "protocol": "ds-agent/1.0",
  "mode": "task",
  "task": {
    "name": "任务名",
    "summary": "一句话描述",
    "vars": {"KEY": "value"},
    "steps": []
  }
}
```

## 步骤字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `action` | 是 | 操作类型 |
| `path` | 大多数必填 | 工作区相对路径 |
| `id` | 否 | 步骤 id |
| `on_error` | 否 | `stop`（默认）/ `continue` |
| `note` | 否 | 人类可读说明 |

## 操作

- `mkdir(path)`：创建目录及其所有父目录。已存在不报错。
- `write_file(path, content)`：写入完整文件。原文件自动备份。
- `edit_file(path, old_text, new_text)`：局部替换，`old_text` 必须唯一。
- `append_file(path, content)`：追加内容。
- `delete_file(path)`：删除文件（先备份）。
- `move_file(path, to)`：移动或重命名。
- `copy_file(path, to)`：复制。
- `run_code(path, timeout?)`：运行 `.py` / `.js` / `.sh`。
- `read_file(path, max_chars?)`：读取文件内容。
- `list_dir(path?)`：列出目录。

## 模板变量

`task.vars` 里的键可以在 `path` 与 `content` 中用 `{{KEY}}` 引用：

```json
{
  "vars": {"PROJECT": "myapp", "VERSION": "1.0"},
  "steps": [
    {"action": "write_file", "path": "{{PROJECT}}/version.txt",
     "content": "v{{VERSION}}"}
  ]
}
```

## 执行语义

1. **顺序**：按 steps 顺序执行。
2. **失败**：默认停止。`on_error: "continue"` 时继续。
3. **反馈**：所有步骤结果汇总后一并回传。
4. **审批**：步骤数超过阈值先做整批审批；否则逐项审批。
5. **兼容**：也接受单步格式 `{"action": "...", ...}`。
6. **无需执行**：`task.steps` 为空时合法。
