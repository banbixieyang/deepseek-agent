# 后端对比与切换指南

## 对比

| 后端 | 默认 | 依赖 | 网络 | 风险 |
|---|---|---|---|---|
| `api` DeepSeek 官方 | ✅ | `requests` | 需要 | 低 |
| `web` 浏览器自动化 | ❌ | `[web]` extras + Firefox + `ds_read.py` | 需要 | 高，可能违反 ToS |
| `openai` OpenAI 兼容 | ❌ | `requests` | 需要 | 视服务商 |
| `ollama` 本地 | ❌ | `requests` + 本地 Ollama | 本地 | 低 |

## 切换

编辑 `config/config.yaml`：

```yaml
backend:
  type: api          # api | web | openai | ollama
```

或环境变量：

```bash
export DS_AGENT_BACKEND=api
```

## 各后端要点

### api（推荐）

```yaml
backend:
  type: api
  api:
    provider: deepseek
    api_key: ""            # 留空则读 DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com
    model: deepseek-chat
    temperature: 0.7
    max_tokens: 4096
    timeout: 120
    retry: 3
    min_interval_seconds: 1.0
```

### web（高风险）

启用前请阅读 README 顶部免责声明。必须同时设置 `enabled: true` 与
`acknowledge_risk: true`，否则启动会被拒绝。

```yaml
backend:
  type: web
  web:
    enabled: true
    acknowledge_risk: true
    ds_read_script: /abs/path/to/ds_read.py
    python_executable: python
    url: https://chat.deepseek.com
    window_titles: ["Mozilla Firefox", "Firefox"]
```

### openai（OpenAI 兼容）

把 `provider` 改为 `openai`，`base_url` 指向你的服务（例如自建中转）。

### ollama（本地）

```yaml
backend:
  type: ollama
  api:
    provider: ollama
    base_url: http://127.0.0.1:11434/v1
    model: llama3
```

不需要 API Key。

## 自定义后端

实现 `bridge/base.py` 的 `BrainBackend` 协议，在 `bridge/factory.py` 里注册即可。
执行循环不感知具体后端。
