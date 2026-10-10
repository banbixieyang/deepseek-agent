# 更新日志

本项目遵循语义化版本。

## [Unreleased]

### 文档

- 新增 `docs/architecture.md`、`docs/backends.md`、`docs/faq.md`
- 新增 `SECURITY.md`、`CODE_OF_CONDUCT.md`、`.editorconfig`
- README 增加“作者”节与作者署名

### 变更

- `LICENSE` 版权行与 `pyproject.toml` 的 authors 统一为 **半壁斜阳-_-**
- CI 增加 Python 3.13 与 `ruff format --check`

## [0.1.0] - 2025-01-01

> 作者：**半壁斜阳-_-**

### 新增

- `BrainBackend` 协议：`api` / `web` / `openai` / `ollama` 四种后端
- 默认后端：DeepSeek 官方 API（无需浏览器、无需 GUI 库）
- 网页后端风险确认门：未确认风险时启动直接拒绝
- `python -m ds_agent.config_cli`：命令行配置向导
- `python -m ds_agent.admin`：Web 配置管理面板
- `python scripts/setup.py`：一键环境搭建；`--uninstall` 清理
- `python app.py --audit`：只打印将发送内容，不实际发送
- 协议层：`parser` / `schema` / `expand` / `preview` 拆分
- 资源外置：`resources/{spec,prompts,examples}`
- 测试：协议、展开、预览、完成判定、工作区隔离、审批、后端工厂、API mock
- CI：GitHub Actions（Linux / macOS / Windows × Python 3.10–3.12）
- pre-commit：ruff + 常用钩子

### 变更

- 配置模块 import 不再产生副作用
- `print` / `traceback.print_exc` 替换为 `logging`
- GUI 依赖（`pyautogui` / `pyperclip` / `pygetwindow`）降为可选 extras
- 原版 `C:\Users\Lenovo\...` 硬编码路径移除，改为配置项 + 环境变量

### 移除

- 启动时的 Ollama 强制检查（原版为死代码，未实际调用本地推理）

### 安全

- 日志不记录完整 API Key，只保留前 4 位 + `****`
- 网页后端默认关闭，必须显式 `enabled: true` 且 `acknowledge_risk: true`
- `.gitignore` 覆盖 `.env` / `config.yaml` / `_internal/` / `workspace/*` / `*.bak` / `*.log`
- README 顶部醒目免责声明，声明与 DeepSeek 官方无关联
