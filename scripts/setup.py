# 便捷入口：python scripts/setup.py
#
# 逻辑在 src/ds_agent/setup.py。
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
for path in (SRC, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from ds_agent.setup import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
