# 网页自动化后端指南

> 免责声明：网页自动化可能违反 DeepSeek 服务条款，存在账号被封禁风险。仅供个人学习研究，请使用小号并控制调用频率。使用后果由使用者自行承担。

## 何时使用

优先使用默认的 API 后端。只有在下列场景才考虑网页后端：

- 没有 API Key，但可以手工登录网页版
- 只是个人学习，不涉及批量、并发、商业用途
- 已充分理解并接受风险

## 前置条件

1. Python 3.10+
2. Firefox
3. 外部脚本 ds_read.py
4. pyautogui / pyperclip / pygetwindow

## 步骤

### 1. 装 GUI 依赖

    scripts\start.bat --with-web

它会运行 .venv\Scripts\python.exe -m pip install -e .[web]。

注意：一定要装进 .venv，不是系统 Python。

### 2. 准备 ds_read.py

ds_read.py 是读取 DeepSeek 网页回复的外部脚本，本项目不内置、不分发。

三种方式任选：

    scripts\start.bat --ds-read-url  <下载地址>
    scripts\start.bat --ds-read-file <本地路径>
    把 ds_read.py 手动放到 _internal\ds_read.py

下载或复制后的位置固定为 _internal/ds_read.py。启动器会自动把这个路径写入 config/config.yaml 的 backend.web.ds_read_script。

### 3. 打开 Firefox 并登录

登录 https://chat.deepseek.com，保持窗口不最小化。

### 4. 启用并确认风险

编辑 config/config.yaml：

    backend:
      type: web
      web:
        enabled: true
        acknowledge_risk: true
        ds_read_script: <绝对路径>
        window_titles:
          - Mozilla Firefox
          - Firefox

或运行 python -m ds_agent.config_cli。启动时若未设置 acknowledge_risk 会直接拒绝运行。

### 5. 启动

    scripts\start.bat

## 诊断

如果启动失败，依次检查：

1. Firefox 是否打开且登录 DeepSeek
2. ds_read.py 是否存在于 _internal/
3. 手动运行 ds_read.py 能否正常输出

    .venv\Scripts\python.exe _internal\ds_read.py --token-only

4. 运行诊断脚本：

    .venv\Scripts\python.exe scripts\diagnose_firefox.py

## 常见问题

问：找不到 Firefox 窗口？
答：窗口标题必须包含 backend.web.window_titles 中的某一项，默认是 Mozilla Firefox 和 Firefox。

问：ds_read.py 报未配置？
答：检查 config/config.yaml 的 backend.web.ds_read_script 是否指向 _internal/ds_read.py 的绝对路径。

问：登录后马上掉线？
答：网页后端依赖浏览器已登录状态。请保持 Firefox 窗口不关闭、不最小化、不退出登录。
