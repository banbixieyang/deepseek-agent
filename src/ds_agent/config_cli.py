# 命令行配置向导。
#
# 首次启动引导：选择后端 → 填写凭据 → 保存配置。
# 选网页后端时必须输入 I understand 显式确认风险。
from __future__ import annotations

from ds_agent.bridge.factory import RISK_TEXT
from ds_agent.config import load_config, project_root, save_config
from ds_agent.schema import AppConfig

API_KEY_HELP = "获取地址：https://platform.deepseek.com/api_keys"
RISK_CONFIRM_TOKEN = "I understand"


def _ask(prompt: str, default: str = "") -> str:
    try:
        raw = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(1)
    return raw or default


def _write_env(key: str, value: str) -> None:
    # 把 key=value 写入项目根目录的 .env（不存在则创建）。
    env_path = project_root() / ".env"
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    target = key + "=" + value
    replaced = False
    for i, line in enumerate(lines):
        if line.startswith(key + "="):
            lines[i] = target
            replaced = True
            break
    if not replaced:
        lines.append(target)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def confirm_risk() -> bool:
    # 打印风险声明，要求输入确认短语。
    print(RISK_TEXT)
    try:
        ans = input("请输入 " + RISK_CONFIRM_TOKEN + " 表示已理解并接受风险 > ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    return ans == RISK_CONFIRM_TOKEN


def setup_api(cfg: AppConfig) -> None:
    print("\n选择 API provider：")
    print("  1. DeepSeek 官方（推荐）")
    print("  2. OpenAI 兼容")
    print("  3. Ollama 本地")
    choice = _ask("请输入 [1/2/3]（默认 1）: ", "1")

    if choice == "2":
        cfg.backend.api.provider = "openai"
        cfg.backend.api.base_url = _ask("base_url > ", "https://api.openai.com/v1")
        cfg.backend.api.model = _ask("model > ", "gpt-4o-mini")
    elif choice == "3":
        cfg.backend.api.provider = "ollama"
        cfg.backend.api.base_url = _ask("base_url > ", "http://127.0.0.1:11434/v1")
        cfg.backend.api.model = _ask("model > ", "llama3")
    else:
        cfg.backend.api.provider = "deepseek"
        cfg.backend.api.base_url = _ask("base_url > ", "https://api.deepseek.com")
        cfg.backend.api.model = _ask("model > ", "deepseek-chat")

    if cfg.backend.api.provider != "ollama":
        print("\n" + API_KEY_HELP)
        key = _ask("API Key（留空表示稍后从环境变量读取）: ")
        if key:
            _write_env("DEEPSEEK_API_KEY", key)
            print("已写入 .env：DEEPSEEK_API_KEY=****")
        else:
            print("未填写 API Key，请确保环境变量 DEEPSEEK_API_KEY 已设置。")

    cfg.backend.type = "api"
    print("已选择 API 后端（provider=" + cfg.backend.api.provider + "）")


def setup_web(cfg: AppConfig) -> None:
    cfg.backend.type = "web"
    cfg.backend.web.enabled = True
    cfg.backend.web.acknowledge_risk = True

    script = _ask("ds_read.py 绝对路径（可留空稍后填写）: ")
    if script:
        cfg.backend.web.ds_read_script = script
    title = _ask("Firefox 窗口标题（可留空）: ")
    if title:
        cfg.backend.web.window_titles = [title]
    print("已启用网页后端。请遵守 DeepSeek 服务条款，勿用主力账号。")


def main(argv: list[str] | None = None) -> int:
    print("=" * 60)
    print("  ds-agent 配置向导")
    print("=" * 60)
    print()
    print("请选择要使用的后端：")
    print("  1. API（推荐，无需浏览器）")
    print("  2. 网页自动化（有风险，可能违反 ToS）")
    print("  3. 退出")

    choice = _ask("请输入 [1/2/3]: ")
    if choice == "3":
        print("已退出")
        return 0

    cfg = load_config()

    if choice == "2":
        if not confirm_risk():
            print("未确认风险，已中止。")
            return 1
        setup_web(cfg)
    else:
        setup_api(cfg)

    path = save_config(cfg)
    print()
    print("已保存到 " + str(path))
    print("请重启主程序以生效：python app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
