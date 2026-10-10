# 常见问题

## 不装 Firefox 能用吗？

能。默认 `api` 后端只依赖 `requests`，不需要浏览器。

## `ds_read.py` 是什么？可以不分发吗？

网页后端读取 DeepSeek 网页回复的外部依赖脚本，本项目不分发。
仅当 `backend.type=web` 时才需要。

## 为什么没有本地 LLM 推理？

推理由后端承担。原版的 Ollama 启动检查是死代码，已移除；
`ollama` 现在作为可选后端保留。

## 路径越界报错怎么办？

所有文件操作限制在 `workspace_dir` 内。需要操作外部文件时，先复制进工作区。

## 日志里没看到完整 API Key？

这是设计。日志只记录前 4 位 + `****`。

## CI 上 ruff format --check 报错？

本地运行一次 `ruff format src tests` 即可。

## 如何切换到 Playwright 驱动？

目前 `bridge/web/browser.py` 的 Playwright / CDP 是占位实现，
仅 `pyautogui` 可用。若你需要，请提 Issue 或自行扩展。

## 遇到“未确认风险”报错？

网页后端默认关闭。请在 `config.yaml` 里同时设置：

```yaml
backend:
  type: web
  web:
    enabled: true
    acknowledge_risk: true
```
