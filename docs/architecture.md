# 架构说明

## 分层

```
┌─────────────────────────────────────────────────┐
│  终端 REPL  app.py / ds_agent.app               │
├─────────────────────────────────────────────────┤
│  执行循环  executor/loop.py                     │
│    · 与后端对话                                 │
│    · 解析 ds-agent 协议                         │
│    · 整批 / 逐项审批                            │
│    · 执行并反馈                                 │
├─────────────────────────────────────────────────┤
│  后端协议  bridge/base.py BrainBackend          │
│    api  ·  web  ·  openai  ·  ollama            │
│    由 bridge/factory.py 依据配置创建            │
├─────────────────────────────────────────────────┤
│  执行器  executor/runner.py                     │
│  工具    tools/{filesystem,shell}               │
│  审批    core/approval.py                       │
│  附件    core/attachments.py                    │
├─────────────────────────────────────────────────┤
│  配置  config.py  +  schema.py                  │
│  日志  logging_setup.py                         │
│  资源  resources/{spec,prompts,examples}        │
└─────────────────────────────────────────────────┘
```

## 数据流

1. 用户输入 → `ExecutionLoop.run`
2. 若输入已含 ds-agent 协议 → 跳过大脑，直接执行
3. 否则调用 `backend.ask(contract + 用户输入)`
4. 解析协议 → `expand_task` 展开变量 → `render_preview` 预览
5. 步骤多时整批审批，否则逐项审批
6. `TaskRunner` 顺序执行 → `format_results` 汇总
7. 结果作为下一轮输入发送回后端，循环直到结束信号或到达最大轮次

## 关键设计

- **无副作用 import**：`ds_agent.config` 不创建目录、不读文件
- **依赖倒置**：执行循环只依赖 `BrainBackend` 协议
- **工作区隔离**：`tools/_common.resolve_in_workspace` 强制越界检查
- **可测**：协议、展开、预览、完成判定、审批、后端工厂均有单测
- **资源外置**：协议规范与提示词放 `resources/`，用 `importlib.resources` 读取
