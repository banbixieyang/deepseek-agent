<<PREFIX>>

你上一次的回复没有包含符合规范的 ds-agent 协议块。
检测到的问题：<<ISSUE>>

<<TONE>>一个 ds-agent 代码块，格式如下：

```ds-agent
{
  "protocol": "ds-agent/1.0",
  "mode": "task",
  "task": {
    "name": "任务名",
    "summary": "一句话描述",
    "vars": {"VAR": "value"},
    "steps": [
      {"action": "write_file",
       "path": "hello.py",
       "content": "print('hello')"}
    ]
  }
}
```

【支持的 action】
- mkdir(path): 创建目录
- write_file(path, content): 写完整文件
- edit_file(path, old_text, new_text): 局部修改
- append_file(path, content): 追加内容
- delete_file(path): 删除文件
- move_file(path, to): 移动或重命名
- copy_file(path, to): 复制
- run_code(path, timeout?): 运行代码
- read_file(path, max_chars?): 读取文件
- list_dir(path?): 列出目录

【两种例外情况】
如果你确实不需要执行任何操作（纯讨论、回答问题、确认收到）：

方案 A：在回复里明确写出"无需执行"四个字
方案 B：在回复末尾附上：

```ds-agent
{"protocol": "ds-agent/1.0", "mode": "task",
  "task": {"name": "无需执行", "steps": []}}
```

否则执行器会一直等待你的协议块。
