# 完成信号判定。
#
# 输入是 LLM 的纯文本回复，输出是 bool。
# 该模块不依赖网络、浏览器与工作区，可单测。
from __future__ import annotations

# 明确表示结束的短语
END_MARKERS = (
    "无需执行",
    "不需要执行",
    "没有其他",
    "任务完成",
    "已完成",
    "搞定",
    "完毕",
    "结束",
    "等待你的",
    "请告诉我下一步",
    "还有什么",
    "还有别的",
)

# 出现在前部时表示仍要继续执行的动词
ACTION_HINTS = (
    "保存到",
    "写入",
    "运行",
    "创建",
    "修改",
    "替换",
    "执行",
    "测试",
    "新建",
    "删除",
    "mkdir",
    "write_file",
    "edit_file",
    "run_code",
)


def looks_like_finish(text: str) -> bool:
    # 判断回复是否意味着本轮结束。
    #
    # 判定顺序：
    #   1. 含 ds-agent 或 json 代码块 → 不是结束
    #   2. 尾部出现结束短语 → 是
    #   3. 头部出现执行动词 → 不是
    #   4. 头部出现结束短语 → 是
    #   5. 非常短（<150 字）→ 视为结束
    if not text:
        return True

    if "```ds-agent" in text or "```json" in text:
        return False

    tail = text[-200:]
    for marker in END_MARKERS:
        if marker in tail:
            return True

    head = text[:300]
    for word in ACTION_HINTS:
        if word in head:
            return False

    for marker in END_MARKERS:
        if marker in head:
            return True

    return len(text) < 150
