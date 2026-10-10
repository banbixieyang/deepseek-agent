# 执行循环。面向 BrainBackend 协议，不直接依赖具体后端。
from __future__ import annotations

from ds_agent.bridge import BrainBackend, create_backend
from ds_agent.config import get_config
from ds_agent.core.approval import ApprovalManager
from ds_agent.executor.feedback import format_results
from ds_agent.executor.finish import looks_like_finish
from ds_agent.executor.protocol import (
    expand_task,
    extract_protocol,
    render_preview,
)
from ds_agent.executor.runner import TaskRunner
from ds_agent.logging_setup import get_logger
from ds_agent.resources import load_text
from ds_agent.schema import AppConfig

logger = get_logger(__name__)

_EXECUTOR_CONTRACT = None
_FORMAT_REMINDER = None


def executor_contract() -> str:
    # 懒加载系统契约提示词。
    global _EXECUTOR_CONTRACT
    if _EXECUTOR_CONTRACT is None:
        _EXECUTOR_CONTRACT = load_text("prompts/executor_contract.md")
    return _EXECUTOR_CONTRACT


def format_reminder_template() -> str:
    # 懒加载格式提醒模板。
    global _FORMAT_REMINDER
    if _FORMAT_REMINDER is None:
        _FORMAT_REMINDER = load_text("prompts/format_reminder.md")
    return _FORMAT_REMINDER


def _indent(text: str, prefix: str = "   ") -> str:
    if not text:
        return ""
    return "\n".join(prefix + line for line in text.split("\n"))


def build_format_reminder(reply: str, attempt: int) -> str:
    # 根据违规情况构造提醒文本。
    issues = []
    if "```ds-agent" not in reply:
        issues.append("没有 ds-agent 代码块")
    if "```json" in reply and "```ds-agent" not in reply:
        issues.append("用了 json 代码块，应该用 ds-agent 代码块")
    if "{" not in reply or "}" not in reply:
        issues.append("没有 JSON 对象")
    if "action" not in reply and "steps" not in reply:
        issues.append("缺少 action 或 steps 字段")
    if "protocol" not in reply and "task" not in reply:
        issues.append("缺少 protocol 或 task 顶层字段")
    issue_str = "；".join(issues) if issues else "未检测到符合规范的协议"

    if attempt == 1:
        tone = "请补充"
        prefix = "【格式提醒】"
    elif attempt == 2:
        tone = "请务必补充"
        prefix = "【再次提醒-格式错误】"
    else:
        tone = "这是最后一次提醒，请严格按格式补充"
        prefix = "【最后一次提醒-格式错误】"

    template = format_reminder_template()
    return (
        template.replace("<<PREFIX>>", prefix)
        .replace("<<ISSUE>>", issue_str)
        .replace("<<TONE>>", tone)
    )


class ExecutionLoop:
    # 执行循环：与后端对话、解析协议、执行、反馈。

    def __init__(
        self,
        cfg: AppConfig | None = None,
        backend: BrainBackend | None = None,
        audit: bool = False,
    ) -> None:
        self.cfg = cfg or get_config()
        self.backend: BrainBackend = backend or create_backend(self.cfg)
        self.approval = ApprovalManager()
        self.runner = TaskRunner(approval_mgr=self.approval)
        self.audit = audit

    @property
    def bridge(self) -> BrainBackend:
        # 兼容旧命名：返回当前后端。
        return self.backend

    def start(self) -> None:
        self.backend.start()

    def stop(self) -> None:
        try:
            self.backend.stop()
        except Exception:
            logger.exception("后端停止失败")

    # ---------- 主流程 ----------

    def run(self, user_input: str, force_new_session: bool = False) -> None:
        print("\n" + "=" * 60)
        print("用户：" + user_input)
        print("=" * 60)

        direct_task = extract_protocol(user_input)
        if direct_task:
            print("\n[检测] 输入里包含 ds-agent 协议，跳过后端直接执行")
            reply = user_input
        else:
            if force_new_session:
                try:
                    self.backend.new_conversation()
                except Exception as exc:
                    logger.exception("创建新会话失败")
                    print("\n创建新会话失败：" + str(exc))
                    return

            print("\n[第 0 轮] 转发用户消息给后端")
            try:
                reply = self._ask(user_input, label="原始需求", prepend=executor_contract())
            except Exception as exc:
                logger.exception("发送失败")
                print("\n发送失败：" + str(exc))
                return
            print("\n后端回复：")
            print(_indent(reply))

        if self.audit:
            print("\n[AUDIT] 当前为审查模式，未执行任何步骤")
            return

        format_violation_count = 0
        max_rounds = int(self.cfg.loop.max_rounds)
        max_retry = int(self.cfg.loop.max_format_retry)
        threshold = int(self.cfg.loop.batch_approval_threshold)

        for round_num in range(1, max_rounds + 1):
            print("\n" + "-" * 60)
            print("第 " + str(round_num) + " 轮")
            print("-" * 60)

            task = extract_protocol(reply)

            if not task:
                if looks_like_finish(reply):
                    print("   检测到完成信号，任务结束")
                    break

                format_violation_count += 1
                if format_violation_count > max_retry:
                    print("\n   后端连续 " + str(max_retry) + " 次未遵守格式，放弃本轮")
                    print("   建议：用 /new 开启新会话重试")
                    break

                label_num = "（第 " + str(format_violation_count) + "/" + str(max_retry) + " 次）"
                print("   未检测到协议块 " + label_num)
                print("   重发格式提醒...")

                reminder = build_format_reminder(reply, format_violation_count)
                try:
                    reply = self._ask(
                        reminder,
                        label="第 "
                        + str(round_num)
                        + " 轮格式提醒 ("
                        + str(format_violation_count)
                        + "/"
                        + str(max_retry)
                        + ")",
                    )
                except Exception as exc:
                    logger.exception("发送格式提醒失败")
                    print("   发送失败：" + str(exc))
                    return
                print("\n后端回复：")
                print(_indent(reply))
                continue

            format_violation_count = 0
            task = expand_task(task)

            print()
            print(render_preview(task))
            print()

            if len(task.steps) > threshold:
                if not self.approval.ask_batch(len(task.steps)):
                    print("   用户拒绝执行")
                    break

            print("   开始执行（" + str(len(task.steps)) + " 步）")
            results = self.runner.run(task)

            feedback = format_results(task, results)
            print("\n   反馈给后端...")
            try:
                reply = self._ask(feedback, label="第 " + str(round_num) + " 轮反馈")
            except Exception as exc:
                logger.exception("发送反馈失败")
                print("   发送失败：" + str(exc))
                return
            print("\n后端回复：")
            print(_indent(reply))
        else:
            print("\n达到最大轮次 " + str(max_rounds))

    # ---------- 发送辅助 ----------

    def _ask(self, text: str, label: str, prepend: str = "") -> str:
        if self.audit:
            header = "[AUDIT] 将要发送给后端（" + label + "）："
            print("\n" + header)
            print("-" * 60)
            print(text if not prepend else prepend + "\n\n" + text)
            print("-" * 60)
            return ""
        return self.backend.ask(
            text,
            label=label,
            approval_mgr=self.approval,
            prepend=prepend,
        )
