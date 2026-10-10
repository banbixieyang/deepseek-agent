> **⚠️ 免责声明（请先阅读）**
>
> - 本项目通过**浏览器自动化**访问 DeepSeek 网页版时，**可能违反 DeepSeek 的服务条款**。
> - 本项目**仅供个人学习与研究**，**禁止**商业用途、批量请求、绕过付费或规避平台限制。
> - 使用者需**自行承担**账号封禁、服务中断、数据丢失等一切后果。
> - 项目**不对任何滥用行为负责**。
> - 项目**与 DeepSeek 官方无任何关联**，未获得其授权、认可或赞助。
> - 项目**不包含、不分发、不破解** DeepSeek 的任何私有接口、加密算法或技术保护措施。
>
> **强烈建议**：
> - 优先使用 **DeepSeek 官方 API**（默认后端）。
> - 如确实需要网页自动化，请使用**小号或专用账号**，不要用主力账号。
> - **控制调用频率**，不要高频、并发、批量调用。

# ds-agent · 可审批的本地 Agent 执行器

把大模型当“大脑”、本地当“手脚”的可审批 Agent 桥接器。**默认走 DeepSeek 官方 API**，可选网页自动化后端（高风险）。

## 它是什么

- 你在终端输入需求
- 程序把需求发给“大脑”后端（默认 DeepSeek 官方 API）
- 大脑返回结构化协议块 `ds-agent`（JSON）
- 本地执行器机械执行协议里的步骤（读写文件、运行代码等）
- 执行结果回传，循环直到任务完成
- 全程人工审批：发送前可修改，写入前可逐项确认

## 后端对比

| 后端 | 默认 | 依赖 | 风险 |
|---|---|---|---|
| `api`（DeepSeek 官方 API） | ✅ 是 | 仅 `requests` | 低，遵守官方 ToS |
| `web`（浏览器自动化） | ❌ 否 | `pyautogui` + Firefox + `ds_read.py` | 高，可能违反 ToS |
| `openai`（OpenAI 兼容） | ❌ 否 | `requests` | 视服务商而定 |
| `ollama`（本地 Ollama） | ❌ 否 | `requests` + 本地 Ollama | 低 |

## 架构

```
终端 REPL  (app.py)
    │
    ▼
ExecutionLoop ──► BrainBackend (协议)
    │                 │
    │                 ├── DeepSeekAPIBackend  (默认, api)
    │                 ├── DeepSeekWebBackend  (高风险, web)
    │                 ├── OpenAICompatBackend (openai)
    │                 └── OllamaBackend       (ollama)
    │
    ├── Protocol Parser  (ds-agent/1.0)
    ├── ApprovalManager  (发送审批 / 写入审批)
    └── TaskRunner ──► Tools (filesystem / shell)
```

## 一键启动（推荐）

Windows：

    scripts\start.bat

macOS / Linux：

    chmod +x scripts/start.sh
    ./scripts/start.sh

首次运行会自动建立 .venv、装依赖、问你选后端、保存配置、启动主程序。

详细步骤见 QUICKSTART.md；网页后端见 docs/web-backend.md。

### 手动启动（等价流程）

    git clone <your-repo-url> ds-agent
    cd ds-agent
    python scripts/setup.py
    python -m ds_agent.config_cli
    python app.py

### 网页后端专用参数

    scripts\start.bat --with-web                          装 GUI 依赖
    scripts\start.bat --with-web --ds-read-url <URL>      下载 ds_read.py
    scripts\start.bat --with-web --ds-read-file <PATH>    使用本地 ds_read.py

API Key 只从环境变量 `DEEPSEEK_API_KEY` 或 `config/config.yaml` 读取，**绝不硬编码**。

## 启用网页后端（不推荐）

如果你确实需要网页自动化：

```bash
pip install "ds-agent[web]"
python scripts/setup.py --with-web
```

然后在 `config/config.yaml` 里显式开启：

```yaml
backend:
  type: web
  web:
    enabled: true
    acknowledge_risk: true   # 必须显式确认
```

未设置 `acknowledge_risk: true` 时，程序启动会**直接拒绝**。

## 配置管理

| 入口 | 说明 |
|---|---|
| `python -m ds_agent.config_cli` | 命令行一问一答 |
| `python -m ds_agent.admin` | Web 面板，默认 `127.0.0.1:8765` |

## 日志与审计

- 日志**不记录** API Key，只记录前 4 位 + `****`。
- 网页后端日志会加 `[WEB]` 前缀，提示当前处于高风险模式。
- `python app.py --audit`：只打印将要发送给后端的内容，不实际发送。

## 常见问题

**Q：不装 Firefox 能用吗？**
A：能。默认 `api` 后端不需要浏览器，只依赖 `requests`。

**Q：ds_read.py 是什么？**
A：网页后端读取回复的外部依赖，本项目不分发。仅当 `backend.type=web` 时才需要。

**Q：为什么没有本地 LLM？**
A：推理由后端承担。原版的 Ollama 启动检查是死代码，已移除；`ollama` 现在作为可选后端存在。

**Q：路径越界报错？**
A：所有文件操作限制在工作区内，越界会被拒绝。

## 更多文档

- 架构说明：[`docs/architecture.md`](docs/architecture.md)
- 后端对比与切换：[`docs/backends.md`](docs/backends.md)
- 常见问题：[`docs/faq.md`](docs/faq.md)
- 贡献指南：[`CONTRIBUTING.md`](CONTRIBUTING.md)
- 安全策略：[`SECURITY.md`](SECURITY.md)
- 更新日志：[`CHANGELOG.md`](CHANGELOG.md)
- 作者：[`AUTHORS.md`](AUTHORS.md)

## 协议

完整规范见 `src/ds_agent/resources/spec/ds-agent-1.0.md`。

## 作者

**半壁斜阳-_-**

## 许可证

MIT，见 `LICENSE`。


## 致谢

- **ds_read.py**：来自 [VZService/SKILL_web-ds-read](https://github.com/VZService/SKILL_web-ds-read)，外部网页读取脚本（只读、纯标准库），本项目不分发、不内置。详见 [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)。
- 感谢所有上游依赖与社区贡献者。

## 网络与镜像

首次使用网页后端时，启动器会尝试下载 `ds_read.py`。国内网络通常无法直接访问 `raw.githubusercontent.com`，会出现超时。

**五条可选路径**：

1. **默认**：直接下载（若网络可达）

   ```
   scripts\start.bat --with-web
   ```

2. **使用镜像**（把镜像前缀拼在 GitHub raw 地址前面）

   ```
   scripts\start.bat --with-web --ds-read-url "https://ghproxy.com/https://raw.githubusercontent.com/VZService/SKILL_web-ds-read/main/scripts/ds_read.py"
   ```

   其它可选镜像前缀：`https://gh-proxy.com/`、`https://mirror.ghproxy.com/`。

3. **浏览器手动下载后用本地文件**（最稳）

   - 浏览器打开：https://github.com/VZService/SKILL_web-ds-read/blob/main/scripts/ds_read.py
   - 点击 Raw 按钮，另存为 `ds_read.py`
   - 然后：

   ```
   scripts\start.bat --with-web --ds-read-file "D:\下载路径\ds_read.py"
   ```

4. **手动放置到标准位置**

   把 `ds_read.py` 放到 `_internal\ds_read.py`，然后：

   ```
   scripts\start.bat
   ```

5. **改用 API 后端**（推荐，无需下载任何脚本）

   ```
   .venv\Scripts\python.exe -m ds_agent.config_cli
   ```

   选 1，粘贴 API Key。之后 `scripts\start.bat` 即可。
