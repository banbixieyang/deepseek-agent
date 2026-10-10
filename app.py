# 根目录引导脚本。
#
# 真正的逻辑在 src/ds_agent/app.py。
# 这里只负责把 src/ 加入 sys.path，让 python app.py 可以直接运行。
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")

for path in (SRC, ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from ds_agent.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
