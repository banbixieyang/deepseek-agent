# Web 配置管理面板（FastAPI）。
#
# 默认只监听 127.0.0.1，首次启动生成随机密码并打印。
# 后端选择分区含风险提示，网页后端必须勾选同意才能保存。
from __future__ import annotations

import os
import secrets

from ds_agent.config import load_config, save_config
from ds_agent.schema import AppConfig

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

_HTML_HEAD = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>ds-agent 配置管理</title>
<style>
body{font-family:sans-serif;max-width:720px;margin:32px auto;padding:0 16px;color:#222}
h1{font-size:20px}
h2{font-size:16px;margin-top:24px;border-bottom:1px solid #eee;padding-bottom:4px}
label{display:block;margin:8px 0 4px}
input[type=text],input[type=password],select{width:100%;padding:6px;box-sizing:border-box}
button{margin-top:12px;padding:8px 16px;cursor:pointer}
.risk{background:#ffecec;border:1px solid #f5b7b1;padding:12px;margin:12px 0;white-space:pre-wrap}
.ok{color:#1a7f37}
.err{color:#b42318}
</style>
</head>
<body>
"""

_HTML_FOOT = """
</body>
</html>
"""


def _render_form(cfg: AppConfig, message: str = "", error: str = "") -> str:
    api = cfg.backend.api
    web = cfg.backend.web
    parts: list[str] = [_HTML_HEAD]
    parts.append("<h1>ds-agent 配置管理</h1>")
    if message:
        parts.append('<p class="ok">' + message + "</p>")
    if error:
        parts.append('<p class="err">' + error + "</p>")

    parts.append('<form method="post" action="/save">')
    parts.append("<h2>后端选择</h2>")
    parts.append("<label>后端类型</label>")
    parts.append('<select name="backend_type">')
    for value, text in (
        ("api", "DeepSeek API（推荐）"),
        ("web", "网页自动化（高风险）"),
        ("openai", "OpenAI 兼容"),
        ("ollama", "Ollama 本地"),
    ):
        sel = " selected" if cfg.backend.type == value else ""
        parts.append('<option value="' + value + '"' + sel + ">" + text + "</option>")
    parts.append("</select>")

    parts.append("<h2>API 参数</h2>")
    parts.append("<label>provider</label>")
    parts.append(
        '<input type="text" name="api_provider" value="' + (api.provider or "deepseek") + '">'
    )
    parts.append("<label>base_url</label>")
    parts.append('<input type="text" name="api_base_url" value="' + (api.base_url or "") + '">')
    parts.append("<label>model</label>")
    parts.append('<input type="text" name="api_model" value="' + (api.model or "") + '">')
    parts.append("<label>API Key（留空保持不变，切勿提交到 git）</label>")
    parts.append('<input type="password" name="api_key" value="">')

    parts.append("<h2>网页自动化后端</h2>")
    parts.append(
        '<div class="risk">网页自动化可能违反 DeepSeek 服务条款，存在账号封禁风险。仅供个人学习研究，请使用小号并控制调用频率。</div>'
    )
    parts.append("<label>ds_read.py 路径</label>")
    parts.append('<input type="text" name="web_script" value="' + (web.ds_read_script or "") + '">')
    parts.append(
        '<label><input type="checkbox" name="web_ack" value="1"> 我已阅读并理解网页后端的风险</label>'
    )

    parts.append('<button type="submit">保存</button>')
    parts.append("</form>")
    parts.append(_HTML_FOOT)
    return "".join(parts)


def create_app(password: str | None = None, token: str | None = None):
    # 创建 FastAPI 应用。返回 (app, password)。
    try:
        from fastapi import FastAPI, Form, Request
        from fastapi.responses import HTMLResponse, RedirectResponse
    except ImportError as exc:
        raise RuntimeError(
            "缺少管理面板依赖：" + str(exc) + "。请安装：pip install ds-agent[admin]"
        ) from exc

    app = FastAPI(title="ds-agent admin")
    password = password or os.environ.get("DS_AGENT_ADMIN_PASSWORD") or secrets.token_urlsafe(8)
    token = token or password

    def _check(request: Request) -> bool:
        cookie = request.cookies.get("ds_agent_admin")
        return cookie == token

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        if not _check(request):
            return HTMLResponse(
                _HTML_HEAD
                + "<h1>ds-agent 配置管理</h1>"
                + "<p>请输入访问密码。</p>"
                + '<form method="post" action="/login">'
                + '<input type="password" name="password" placeholder="密码">'
                + '<button type="submit">登录</button></form>'
                + _HTML_FOOT,
                status_code=200,
            )
        cfg = load_config()
        return HTMLResponse(_render_form(cfg))

    @app.post("/login")
    def login(password: str = Form(...)):
        if password != token:
            return HTMLResponse(
                _HTML_HEAD + '<p class="err">密码错误</p>' + _HTML_FOOT, status_code=401
            )
        resp = RedirectResponse(url="/", status_code=303)
        resp.set_cookie("ds_agent_admin", token, httponly=True, samesite="strict")
        return resp

    @app.post("/save")
    def save(
        request: Request,
        backend_type: str = Form("api"),
        api_provider: str = Form(""),
        api_base_url: str = Form(""),
        api_model: str = Form(""),
        api_key: str = Form(""),
        web_script: str = Form(""),
        web_ack: str = Form(""),
    ):
        if not _check(request):
            return RedirectResponse(url="/", status_code=303)

        cfg = load_config()
        cfg.backend.type = backend_type
        if api_provider:
            cfg.backend.api.provider = api_provider
        if api_base_url:
            cfg.backend.api.base_url = api_base_url
        if api_model:
            cfg.backend.api.model = api_model
        if api_key:
            cfg.backend.api.api_key = api_key
        cfg.backend.web.ds_read_script = web_script or cfg.backend.web.ds_read_script

        message = "已保存。请重启主程序生效。"
        error = ""
        if backend_type == "web":
            if web_ack == "1":
                cfg.backend.web.enabled = True
                cfg.backend.web.acknowledge_risk = True
            else:
                cfg.backend.web.enabled = False
                cfg.backend.web.acknowledge_risk = False
                error = "未勾选风险确认，已回退到 API 后端。"
                cfg.backend.type = "api"

        save_config(cfg)
        return HTMLResponse(_render_form(cfg, message=message, error=error))

    @app.get("/health")
    def health():
        return {"ok": True}

    app.state.admin_password = password
    return app, password


def main(argv: list[str] | None = None) -> int:
    try:
        import uvicorn
    except ImportError as exc:
        print("缺少 uvicorn：" + str(exc) + "。请安装：pip install ds-agent[admin]")
        return 1

    host = os.environ.get("DS_AGENT_ADMIN_HOST", DEFAULT_HOST)
    try:
        port = int(os.environ.get("DS_AGENT_ADMIN_PORT", str(DEFAULT_PORT)))
    except ValueError:
        port = DEFAULT_PORT

    app, password = create_app()
    print("=" * 60)
    print("  ds-agent 配置管理面板")
    print("  地址：http://" + host + ":" + str(port))
    print("  访问密码：" + password)
    print("  提示：请勿将本面板暴露到公网。")
    print("=" * 60)
    uvicorn.run(app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
