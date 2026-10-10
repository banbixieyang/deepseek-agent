# ds-agent 重制版计划

本目录是重制版，原版文件保持不动。

作者：**半壁斜阳-_-**

## 分批交付（共 7 批）

- 第 1 批：骨架初始化
- 第 2 批：README、LICENSE、pyproject、.gitignore、配置系统
- 第 3 批：bridge、tools、approval、attachments
- 第 4 批：合规重构与后端抽象（BrainBackend + API 默认 + web 迁移 + 风险门）
- 第 5 批：executor、protocol、resources、tests
- 第 6 批：config_cli、admin、setup、脚本、GitHub 初始化、自检清单
- 第 7 批：作者信息、CI、pre-commit、bridge/web 字段路径修复

## 关键决策

### 移除本地 LLM（Ollama）依赖

原版 `executor/loop.py` 启动时请求 `OLLAMA_HOST/api/tags`，
但整个项目没有任何一处调用本地 LLM 推理。DeepSeek 网页版是大脑，
本地只做执行器，本地 LLM 是死代码。

处理：

- 启动流程不再检查 Ollama。
- `config/config.example.yaml` 中不包含 `ollama_host` 必填项。
- `ollama` 现在作为可选后端保留（`bridge/api/ollama.py`），
  只做诊断页探测，失败不阻塞启动。

### 合规优先：默认 API 后端

- 默认后端 = DeepSeek 官方 API，无需浏览器、无需 GUI 库。
- 网页后端默认关闭，必须显式 `enabled: true` 且 `acknowledge_risk: true`。
- 未确认风险时 `create_backend` 抛 `RiskNotAcknowledgedError`，启动直接拒绝。
- README 顶部醒目免责声明，声明与 DeepSeek 官方无关联。
- GUI 依赖降为 `[project.optional-dependencies].web`。

### 后端抽象

`BrainBackend` 协议（`bridge/base.py`）定义统一接口：

```
start / stop / new_conversation / ask / session_id / kind
```

实现：

- `bridge/api/deepseek.py`：DeepSeek 官方 API（默认）
- `bridge/api/openai_compat.py`：OpenAI 兼容
- `bridge/api/ollama.py`：本地 Ollama
- `bridge/web/deepseek.py`：网页自动化（高风险，默认关闭）

工厂：`bridge/factory.py::create_backend(cfg)`

上层 `executor/loop.py` 只依赖 `BrainBackend`，不感知具体实现。

### 配置模块无副作用

- `ds_agent.config` import 时不创建目录、不读文件、不访问网络。
- 需要配置时显式调用 `load_config()` / `get_config()`。
- 需要目录时显式调用 `ensure_directories()`。

### 日志不泄漏凭据

- API Key 只记录前 4 位 + `****`。
- `traceback.print_exc` 全部替换为 `logger.exception`。

## 安全规则

- 不写入任何真实 API Key、Token、Cookie、密码、会话 id。
- 不覆盖原版文件，所有产物在 `rebuild/` 下。
- 不自动 `git push`，只生成初始化命令。
- `_internal/`、`workspace/`、`*.bak`、`*.log`、真实 `config.yaml` 不入库。

## 已知遗留（后续方向）

- `bridge/web/browser.py` 的 Playwright / CDP 驱动为占位实现
- 审批与管理面板文案尚未 i18n
- `bridge/web/deepseek.py` 的网页自动化逻辑未深度重构，仅迁移与字段修正
