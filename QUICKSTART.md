# 快速开始

3 分钟跑起来。

## 1. 装 Python

需要 Python 3.10 或更高：https://www.python.org/downloads/

Windows 安装时勾选 Add python.exe to PATH。

## 2. 一条命令启动

Windows：

    scripts\start.bat

macOS / Linux：

    chmod +x scripts/start.sh
    ./scripts/start.sh

首次运行会自动建立 .venv、装依赖、问你选后端、保存配置、启动主程序。

## 3. 选择后端

向导会问：

    1. API（推荐，无需浏览器）
    2. 网页自动化（有风险，可能违反 ToS）
    3. 退出

走 API：选 1，粘贴 DeepSeek API Key（https://platform.deepseek.com/api_keys）。

走网页自动化：选 2，然后参见 docs/web-backend.md。

## 4. 在 REPL 里使用

你输入需求，程序把需求发给后端，后端返回 ds-agent 协议，本地执行器执行每一步，写入前会问你 y 或 n，结果回传，循环直到完成。

常用命令：/help、/status、/new、/exit。多行输入用三个双引号包裹。

## 5. 先审查、再执行

    scripts\start.bat --audit

只打印将要发送的内容，不实际发送、不执行任何步骤。

## 常见问题

问：报 No module named pyautogui？
答：你在系统 Python 里装了依赖，但程序跑在 .venv。改用 scripts\start.bat --with-web 让启动器在正确环境安装。

问：.venv 装坏了怎么重来？
答：python scripts/setup.py --uninstall，然后重新 scripts\start.bat。

问：怎么切换后端？
答：python -m ds_agent.config_cli，或 python -m ds_agent.admin 打开网页配置面板（需先 --with-admin）。

## 国内网络：下载 ds_read.py 的替代方案

首次使用网页后端时，启动器会尝试从 `raw.githubusercontent.com` 下载 `ds_read.py`。国内网络**通常无法直接访问该域名**，会超时或报错。

四条路任选：

1. **用镜像**

   ```
   scripts\start.bat --with-web --ds-read-url "https://ghproxy.com/https://raw.githubusercontent.com/VZService/SKILL_web-ds-read/main/scripts/ds_read.py"
   ```

2. **浏览器手动下载后指向本地文件**

   打开 https://github.com/VZService/SKILL_web-ds-read/blob/main/scripts/ds_read.py，点 Raw 另存为 `ds_read.py`，然后：

   ```
   scripts\start.bat --with-web --ds-read-file "D:\下载路径\ds_read.py"
   ```

3. **手动放到标准位置**

   把 `ds_read.py` 放到 `_internal\ds_read.py`，运行 `scripts\start.bat`。

4. **改用 API 后端**（推荐，无需下载）

   ```
   .venv\Scripts\python.exe -m ds_agent.config_cli
   ```

   选 1，粘贴 DeepSeek API Key。
