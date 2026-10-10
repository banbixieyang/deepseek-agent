# 清理运行时数据：_internal、日志、备份。
#
# 不删除 .venv，也不删除 config/config.yaml。
import argparse
import shutil
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ds-agent 清理运行时数据")
    parser.add_argument("--all", action="store_true", help="同时删除 config/config.yaml")
    args = parser.parse_args(argv)

    root = project_root()
    targets = [root / "_internal"]
    if args.all:
        targets.append(root / "config" / "config.yaml")

    for target in targets:
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
            print("已删除目录：" + str(target))
        elif target.is_file():
            try:
                target.unlink()
                print("已删除文件：" + str(target))
            except OSError as exc:
                print("删除失败：" + str(target) + "（" + str(exc) + "）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
