# 交互式主入口。
#
# 用法：
#     python app.py
#     python app.py --audit        只打印将要发送的内容，不实际发送
#     python -m ds_agent
from __future__ import annotations

import argparse
from typing import Any

from ds_agent.config import get_config
from ds_agent.logging_setup import setup_logging

# 三个双引号，避免 JSON 转义歧义。
QUOTE3 = chr(34) * 3

BANNER = """
=========================================================
  ds-agent · 可审批的本地 Agent 执行器
=========================================================
  · 你输入需求 → 程序转发给后端（默认 DeepSeek API）
  · 后端返回 ds-agent 协议
  · 本地执行器机械执行协议里的步骤
  · 执行结果自动反馈，循环直到任务完成
=========================================================
  多行输入：输入三个双引号开始，再次输入三个双引号结束
  直接执行：粘贴合法 ds-agent 协议可跳过后端立即执行
=========================================================
  /new   下一条消息开启新会话
  /status 显示当前状态
  /help   显示帮助
  /exit   退出
=========================================================
"""

HELP = """
------------------------------------------------------------
  帮助
------------------------------------------------------------
  /new [内容]   开启新会话
  /status       显示当前状态
  /help         显示本帮助
  /exit         退出程序

  启动参数：
    --audit     只打印将要发送给后端的内容，不实际发送
------------------------------------------------------------
"""


def read_multiline_input(prompt: str = "\n你 > ") -> str:
    first = input(prompt)
    if first.strip() == QUOTE3:
        print("   （多行模式，输入三个双引号结束）")
        lines: list[str] = []
        while True:
            line = input("   ... ")
            if line.strip() == QUOTE3:
                break
            lines.append(line)
        return "\n".join(lines)
    return first


def print_status(loop: Any, cfg: Any, force_new: bool) -> None:
    print()
    print("------------------------------------------------------------")
    print("  当前状态")
    print("------------------------------------------------------------")
    sid = getattr(getattr(loop, "backend", None), "session_id", None)
    print("  后端类型：" + str(cfg.backend.type))
    print("  会话 id：" + (str(sid) if sid else "（未建立）"))
    if cfg.backend.type == "web":
        print("  [WEB] 当前为网页自动化高风险模式")
    print("  工作区：" + str(cfg.paths.workspace_dir))
    if force_new:
        print("  下一条消息将开启新会话")
    print("------------------------------------------------------------")


def _safe_run(loop: Any, text: str, force_new: bool, logger: Any) -> None:
    try:
        loop.run(text, force_new_session=force_new)
    except KeyboardInterrupt:
        print("\n（中断本轮）")
    except Exception as exc:
        logger.exception("执行出错")
        print("\n执行出错：" + str(exc))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="app.py", description="ds-agent 主程序")
    parser.add_argument("--audit", action="store_true", help="只打印将发送的内容，不实际发送")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    print(BANNER)
    if args.audit:
        print("[AUDIT] 已开启审查模式：不会实际向后端发送内容。\n")

    cfg = get_config()
    logger = setup_logging(cfg)
    logger.info("ds-agent 启动，backend=%s, audit=%s", cfg.backend.type, args.audit)

    try:
        from ds_agent.executor.loop import ExecutionLoop
    except ImportError as exc:
        print("执行器尚未就绪：" + str(exc))
        return 1

    try:
        loop = ExecutionLoop(cfg=cfg, audit=args.audit)
    except Exception as exc:
        logger.exception("初始化失败")
        print("\n初始化失败：" + str(exc))
        return 1

    try:
        loop.start()
    except Exception as exc:
        logger.exception("启动失败")
        print("\n启动失败：" + str(exc))
        return 1

    print("\n" + "=" * 60)
    print("  就绪。输入你的需求开始。（/help 查看命令）")
    print("=" * 60)

    force_new = False
    try:
        while True:
            try:
                user_input = read_multiline_input()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            stripped = (user_input or "").strip()
            if not stripped:
                continue
            if stripped in ("/exit", "/quit"):
                print("再见！")
                break
            if stripped == "/help":
                print(HELP)
                continue
            if stripped == "/status":
                print_status(loop, cfg, force_new)
                continue
            if stripped == "/new":
                force_new = True
                print("   已标记：下一条消息将开启新会话")
                continue
            if stripped.startswith("/new "):
                content = stripped[5:].strip()
                if content:
                    print("   立即用新会话发送")
                    _safe_run(loop, content, True, logger)
                    force_new = False
                    continue

            _safe_run(loop, user_input, force_new, logger)
            force_new = False
    finally:
        try:
            loop.stop()
        except Exception:
            logger.exception("清理资源失败")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
