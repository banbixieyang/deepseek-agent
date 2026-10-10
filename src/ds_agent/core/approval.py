# 审批管理器。
#
# 职责：
#   - 拦截发送给 DeepSeek 的内容
#   - 拦截写入文件的操作
#   - 发送前支持：查看完整内容、补充要求、附加文件/文件夹、完全重写、重置
#   - 写入前支持：逐项同意、本次会话自动同意、查看
#
# 说明：
#   界面文案当前内联为中文，i18n 是后续方向，不改动本模块对外接口。
from __future__ import annotations

from dataclasses import dataclass, field

from ds_agent.logging_setup import get_logger

logger = get_logger(__name__)


@dataclass
class ApprovalResult:
    # 审批结果。
    approved: bool
    # 最终内容（可能被用户修改）。
    text: str = ""
    # 是否发生过修改。
    modified: bool = False
    # 用户附加的说明（可选，便于日志追溯）。
    reason: str = ""


@dataclass
class _BackupNote:
    original: str
    backup: str
    time: str


class ApprovalManager:
    # 交互式审批管理器。
    #
    # 状态：_auto_send / _auto_write 为进程级开关，可通过 reset() 清空。

    def __init__(self) -> None:
        self._auto_send = False
        self._auto_write = False
        self._backups: list[_BackupNote] = field(default_factory=list)  # type: ignore[assignment]
        self._backups = []

    # ---------- 状态管理 ----------

    def reset(self) -> None:
        # 清空所有会话级状态。
        self._auto_send = False
        self._auto_write = False
        self._backups = []

    @property
    def auto_write(self) -> bool:
        return self._auto_write

    # ---------- 发送审批 ----------

    def ask_send(self, text: str, label: str = "消息") -> ApprovalResult:
        # 审批一次发送。返回 ApprovalResult。
        current = text
        modified = False

        while True:
            self._header("发送审批（" + label + "）")
            print("   内容长度：" + str(len(current)) + " 字符")
            if modified:
                print("   （已修改，原始 " + str(len(text)) + " 字符）")
            print()
            self._preview(current, max_len=300)
            print()
            print("   选项：")
            print("     y = 同意发送")
            print("     n = 拒绝")
            print("     v = 查看完整内容")
            print("     e = 补充要求（追加到末尾）")
            print("     f = 附加文件或文件夹")
            print("     w = 完全重写（替换全部内容）")
            print("     r = 重置为原始内容")
            self._sep()

            try:
                ans = input("   请输入 [y/n/v/e/f/w/r]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return ApprovalResult(False, text, modified)

            if ans == "y":
                return ApprovalResult(True, current, modified)
            if ans == "n":
                print("   已拒绝")
                return ApprovalResult(False, text, modified)
            if ans == "v":
                self._header("完整内容")
                print(current)
                self._sep()
                continue
            if ans == "e":
                extra = self._read_block("补充要求")
                if extra:
                    current = current + "\n\n" + extra
                    modified = True
                    print("   已追加 " + str(len(extra)) + " 字符")
                continue
            if ans == "f":
                extra = self._read_attach()
                if extra:
                    current = current + "\n\n" + extra
                    modified = True
                    print("   已附加 " + str(len(extra)) + " 字符")
                continue
            if ans == "w":
                new_text = self._read_block("请输入完整的新内容")
                if new_text:
                    current = new_text
                    modified = True
                    print("   已替换为 " + str(len(new_text)) + " 字符")
                continue
            if ans == "r":
                current = text
                modified = False
                print("   已重置为原始内容")
                continue
            print("   无效输入，请重新输入")

    # ---------- 写入审批 ----------

    def ask_write(
        self,
        path: str,
        content: str,
        exists: bool,
        backup_path: str = "",
    ) -> bool:
        # 审批一次写入。返回是否同意。
        if self._auto_write:
            print("   自动同意写入 " + path)
            return True

        self._header("写入审批")
        print("   文件：" + path)
        print("   大小：" + str(len(content)) + " 字符")
        print("   状态：" + ("将覆盖已有文件" if exists else "新建文件"))
        if backup_path:
            print("   备份：" + backup_path)
        print()
        self._preview(content, max_len=400)
        print()
        print("   选项：")
        print("     y = 同意写入")
        print("     n = 拒绝")
        print("     a = 同意本次会话所有写入")
        print("     v = 查看完整内容")
        self._sep()

        while True:
            try:
                ans = input("   请输入 [y/n/a/v]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                return False

            if ans == "y":
                return True
            if ans == "n":
                print("   已拒绝")
                return False
            if ans == "a":
                self._auto_write = True
                print("   已开启本会话自动同意（写入）")
                return True
            if ans == "v":
                self._header("完整内容")
                print(content)
                self._sep()
                continue
            print("   无效输入，请重新输入")

    def ask_batch(self, step_count: int) -> bool:
        # 步骤较多时的整批审批。
        self._header("整批执行审批（" + str(step_count) + " 步）")
        print("   已在上方显示预览。")
        print("   选项：")
        print("     y = 执行")
        print("     n = 拒绝")
        print("     a = 本会话自动同意所有写入")
        self._sep()
        try:
            ans = input("   请输入 [y/n/a]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        if ans == "a":
            self._auto_write = True
            print("   已开启本会话自动同意（写入）")
            return True
        return ans == "y"

    # ---------- 备份记录 ----------

    def note_backup(self, original: str, backup: str) -> None:
        import time as _time

        self._backups.append(_BackupNote(original, backup, _time.strftime("%H:%M:%S")))

    def list_backups(self) -> list[tuple[str, str, str]]:
        return [(b.original, b.backup, b.time) for b in self._backups]

    # ---------- 内部辅助 ----------

    def _read_block(self, title: str) -> str:
        # 连续两个空行结束输入。
        print()
        print("   --------------------------------------------------")
        print("   " + title + "（连续两个空行结束）")
        print("   --------------------------------------------------")
        lines: list[str] = []
        empty = 0
        while True:
            try:
                line = input("   > ")
            except (EOFError, KeyboardInterrupt):
                break
            if line.strip() == "":
                empty += 1
                if empty >= 2:
                    break
                lines.append("")
            else:
                empty = 0
                lines.append(line)
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines)

    def _read_attach(self) -> str:
        # 读取一个文件或文件夹并生成附加文本。
        from ds_agent.core.attachments import attach_path

        print()
        print("   可输入文件或文件夹路径")
        try:
            raw = input("   路径 > ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""
        if not raw:
            return ""
        return attach_path(raw) or ""

    @staticmethod
    def _header(title: str) -> None:
        print()
        print("-" * 60)
        print("  " + title)
        print("-" * 60)

    @staticmethod
    def _sep() -> None:
        print("-" * 60)

    @staticmethod
    def _preview(text: str, max_len: int = 300) -> None:
        if len(text) <= max_len:
            print(text)
            return
        head = text[:max_len]
        for line in head.split("\n"):
            print("   " + line)
        print("   ...（还有 " + str(len(text) - max_len) + " 字符，输入 v 查看完整）")
