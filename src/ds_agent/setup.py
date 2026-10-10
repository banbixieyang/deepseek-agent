# 一键环境搭建。
#
# 检测 Python 版本 → 创建 .venv → 安装依赖 → 引导配置。
# --uninstall 清理 .venv / _internal / config.yaml。
# 所有依赖只装在项目内 .venv，不写系统 PATH。
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)
VENV_DIRNAME = ".venv"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def check_python() -> None:
    if sys.version_info < MIN_PYTHON:
        raise SystemExit(
            "需要 Python "
            + ".".join(map(str, MIN_PYTHON))
            + " 或更高版本，当前为 "
            + sys.version.split()[0]
        )


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def ensure_venv(root: Path) -> Path:
    venv = root / VENV_DIRNAME
    if venv_python(venv).is_file():
        print("[1/4] 已存在虚拟环境：" + str(venv))
        return venv
    print("[1/4] 创建虚拟环境：" + str(venv))
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    return venv


def install_deps(venv: Path, with_web: bool, with_admin: bool) -> None:
    py = str(venv_python(venv))
    print("[2/4] 升级 pip")
    subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=True)

    extras: list[str] = []
    if with_web:
        extras.append("web")
    if with_admin:
        extras.append("admin")
    target = "." if not extras else ".[" + ",".join(extras) + "]"
    print("[2/4] 安装依赖：" + target)
    subprocess.run([py, "-m", "pip", "install", "-e", target], check=True, cwd=str(project_root()))


def check_ds_read(cfg) -> None:
    script = (cfg.backend.web.ds_read_script or "").strip()
    if not script:
        print("      [提示] 未配置 ds_read.py。默认 API 后端不需要它；启用网页后端时必填。")
        return
    if Path(script).is_file():
        print("      [OK] ds_read.py 存在：" + script)
    else:
        print("      [警告] ds_read.py 不存在：" + script)


def check_firefox() -> None:
    import shutil as _sh

    for name in ("firefox", "firefox.exe"):
        if _sh.which(name):
            print("      [OK] 检测到 Firefox：" + name)
            return
    print("      [提示] 未检测到 Firefox。默认 API 后端不需要它。")


def run_config_cli(venv: Path) -> None:
    py = str(venv_python(venv))
    print("[3/4] 运行配置向导")
    subprocess.run([py, "-m", "ds_agent.config_cli"], cwd=str(project_root()))


def print_next_steps() -> None:
    print("[4/4] 完成。下一步：")
    print("  1. 打开 Firefox 并登录 https://chat.deepseek.com（仅网页后端需要）")
    print("  2. 启动主程序：")
    if os.name == "nt":
        print("       .venv\\Scripts\\python.exe app.py")
    else:
        print("       .venv/bin/python app.py")
    print("  3. 或使用启动脚本：scripts/start.sh 或 scripts/start.ps1")


def uninstall(root: Path) -> int:
    print("清理中...")
    targets = [root / VENV_DIRNAME, root / "_internal", root / "config" / "config.yaml"]
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            print("  已删除目录：" + str(target))
        elif target.is_file():
            try:
                target.unlink()
                print("  已删除文件：" + str(target))
            except OSError as exc:
                print("  删除失败：" + str(target) + "（" + str(exc) + "）")
    print("完成。删除项目目录即完全卸载。")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ds-agent 一键环境搭建")
    parser.add_argument("--with-web", action="store_true", help="安装网页后端的 GUI 依赖")
    parser.add_argument("--with-admin", action="store_true", help="安装 Web 管理面板依赖")
    parser.add_argument(
        "--uninstall", action="store_true", help="清理 .venv / _internal / config.yaml"
    )
    parser.add_argument("--skip-config", action="store_true", help="跳过配置向导")
    args = parser.parse_args(argv)

    root = project_root()

    if args.uninstall:
        return uninstall(root)

    check_python()
    venv = ensure_venv(root)
    install_deps(venv, with_web=args.with_web, with_admin=args.with_admin)

    try:
        from ds_agent.config import load_config

        cfg = load_config()
        check_ds_read(cfg)
        check_firefox()
    except Exception as exc:
        print("      [提示] 配置检测跳过：" + str(exc))

    if not args.skip_config:
        run_config_cli(venv)

    print_next_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
