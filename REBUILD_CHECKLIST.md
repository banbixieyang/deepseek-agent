# 重制版最终自检清单

## 安全

- [ ] 搜索不到 `C:\Users\Lenovo`
- [ ] 搜索不到真实 API Key、Token、Cookie、密码、会话 id
- [ ] 搜索不到 `sk-` 开头的真实 Key
- [ ] `_internal/`、`workspace/*`、`*.bak`、`*.log`、真实 `config.yaml` 均不入库
- [ ] `.gitignore` 覆盖 `.env`、`config.yaml`、`_internal/`、`workspace/*`、`*.bak`、`*.log`
- [ ] 日志中不出现完整 API Key，只出现前 4 位 + `****`
- [ ] `.env.example` 与 `config.example.yaml` 仅含空值/示例

## 合规

- [ ] 默认后端为 `api`，无需浏览器与 GUI 库
- [ ] 网页后端默认关闭，需 `enabled: true` 且 `acknowledge_risk: true`
- [ ] 未确认风险时 `create_backend` 抛 `RiskNotAcknowledgedError`
- [ ] README 顶部有醒目免责声明
- [ ] README 中包含小号建议、频率建议、官方 API 优先建议
- [ ] 所有面向用户的界面注明“与 DeepSeek 官方无关联”
- [ ] 不包含 DeepSeek 商标、logo
- [ ] 不绕过登录 / 验证 / 付费

## 功能

- [ ] `python app.py` 可启动
- [ ] `python app.py --audit` 只打印不发送
- [ ] `python -m ds_agent` 等价入口
- [ ] `python -m ds_agent.config_cli` 引导流程可用
- [ ] `python -m ds_agent.admin` 管理面板可访问
- [ ] `python scripts/setup.py` 一键搭建可运行
- [ ] `python scripts/setup.py --uninstall` 清理 `.venv` / `_internal` / `config.yaml`
- [ ] `scripts/start.sh`、`scripts/start.ps1` 可用
- [ ] `scripts/diagnose_firefox.py` 可用（仅网页后端需要）
- [ ] 支持四种后端：`api` / `web` / `openai` / `ollama`

## 代码质量

- [ ] `config` 模块 import 无副作用
- [ ] 所有外部调用有超时、异常捕获、可读错误
- [ ] 关键函数有类型注解与 docstring
- [ ] `print` 只出现在 REPL 交互与提示中，核心逻辑用 `logging`
- [ ] `traceback.print_exc` 已替换为 `logger.exception`
- [ ] 无硬编码屏幕坐标，均按窗口比例计算

## 测试

- [ ] `pytest` 可在干净环境跑通
- [ ] 测试不依赖 Firefox / DeepSeek / 网络
- [ ] 覆盖：协议解析、变量展开、预览渲染、完成判定、工作区隔离、审批状态、后端工厂、API 后端 mock

## 文档

- [ ] README 让新用户 5 分钟内知道如何安装、配置、启动
- [ ] README 有 ASCII 架构图
- [ ] README 有驱动切换说明
- [ ] README 有常见问题
- [ ] README 链接到 `resources/spec/ds-agent-1.0.md`
- [ ] README 说明 `ds_read.py` 是外部依赖、本项目不分发
- [ ] `REBUILD_PLAN.md` 说明分批交付与决策
- [ ] `GITHUB_INIT.md` 提供初始化命令且不自动 push
