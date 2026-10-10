# Firefox / ds_read.py 诊断脚本。
#
# 仅在使用网页后端时需要。默认 API 后端不需要运行。
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for p in (str(SRC), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)


def check_window() -> bool:
    try:
        import pygetwindow as gw
    except ImportError:
        print("  [SKIP] 未安装 pygetwindow（仅网页后端需要）")
        return False
    for title in ("Mozilla Firefox", "Firefox"):
        try:
            windows = gw.getWindowsWithTitle(title)
        except Exception as exc:
            print("  [ERR] 查找窗口失败：" + str(exc))
            continue
        if windows:
            print("  [OK] 找到窗口：" + windows[0].title)
            return True
    print("  [ERR] 未找到 Firefox 窗口。请打开并登录 DeepSeek。")
    return False


def check_ds_read() -> bool:
    from ds_agent.config import load_config
    cfg = load_config()
    script = (cfg.backend.web.ds_read_script or "").strip()
    if not script:
        print("  [ERR] 未配置 ds_read.py 路径")
        return False
    if not Path(script).is_file():
        print("  [ERR] ds_read.py 不存在：" + script)
        return False

    print("  [..] 运行 ds_read.py --token-only")
    try:
        result = subprocess.run(
            [cfg.backend.web.python_executable, script, "--token-only"],
            capture_output=True, text=True, timeout=60,
        )
    except Exception as exc:
        print("  [ERR] 调用失败：" + str(exc))
        return False
    if result.returncode != 0:
        print("  [ERR] 返回码 " + str(result.returncode))
        print("  stdout：" + (result.stdout or "")[:300])
        print("  stderr：" + (result.stderr or "")[:300])
        return False
    print("  [OK] " + (result.stdout or "").strip())
    return True


def main() -> int:
    print("ds-agent 网页后端诊断")
    print("-" * 40)
    print("[1] 检查 Firefox 窗口")
    ok_win = check_window()
    print("[2] 检查 ds_read.py")
    ok_read = check_ds_read()
    print("-" * 40)
    if ok_win and ok_read:
        print("结果：可以启用网页后端。")
        return 0
    print("结果：网页后端尚不可用。默认 API 后端不受影响。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
