# 致谢与第三方归属

本项目感谢以下外部组件与社区工具的贡献。

## ds_read.py

- 项目：VZService/SKILL_web-ds-read
- 仓库：https://github.com/VZService/SKILL_web-ds-read
- 脚本入口：scripts/ds_read.py
- 用途：把 DeepSeek 网页版（chat.deepseek.com）的对话读成可阅读文本，供网页自动化后端使用。
- 特性：只读——不发送消息、不删除会话、不改标题；纯 Python 标准库，无需安装任何包。
- 归属：外部脚本，本项目不分发、不内置、不打包。
- 许可：遵循其仓库声明的许可，与本项目 MIT 许可无关。使用者需自行确认其许可与来源合法。
- 内置下载地址（可在 config.yaml 覆盖）：
  - https://raw.githubusercontent.com/VZService/SKILL_web-ds-read/main/scripts/ds_read.py
- 免责：本项目不对该脚本的正确性、安全性、许可合规性做任何担保。

## 上游依赖

- PyYAML：YAML 解析，MIT 许可。
- requests：HTTP 客户端，Apache-2.0 许可。
- pyautogui / pyperclip / pygetwindow：网页后端 GUI 依赖，BSD 类许可（可选安装）。
- FastAPI / uvicorn / Jinja2：管理面板依赖（可选安装）。
- Playwright：浏览器驱动扩展（可选安装）。

## DeepSeek

- 本项目为第三方工具，与 DeepSeek 官方无任何关联，未获得其授权、认可或赞助。
- 本项目不包含、不分发、不破解 DeepSeek 的任何私有接口、加密算法或技术保护措施。
- DeepSeek 商标归其权利人所有，本仓库不使用其商标或 logo。

## 社区

- 感谢所有提交 Issue、Pull Request、文档修订与建议的贡献者。
- 名单见 AUTHORS.md。
