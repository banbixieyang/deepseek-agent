# DeepSeek 网页版桥接（网页自动化后端，高风险）。
#
# 组合 BrowserDriver（鼠标键盘）+ DsReadClient（读回复），
# 对外暴露 start / stop / new_conversation / ask。
# 由 bridge.factory 在 backend.type=web 且用户已确认风险时创建。
from __future__ import annotations

import time
from typing import Any

from ds_agent.bridge.web.browser import BrowserDriver, create_driver
from ds_agent.bridge.web.ds_read import DsReadClient, DsReadError
from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


class DeepSeekWebBackend:
    # 与 DeepSeek 网页版交互的桥接器。

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self.driver: BrowserDriver = create_driver(cfg)
        self.reader = DsReadClient(cfg)
        self.session_id: str | None = cfg.backend.web.session_id or None
        self._last_reply_id: str | None = None
        self._last_send_time: float = 0.0

    @property
    def kind(self) -> str:
        return "web"

    # ---------- 生命周期 ----------

    def start(self) -> None:
        # 检查 ds_read.py、浏览器窗口，并做一次健康检查。
        if not self.reader.is_configured():
            raise RuntimeError(
                "ds_read.py 未配置或不存在："
                + (self.reader.script_path or "(空)")
                + "\n请在 config/config.yaml 的 backend.web.ds_read_script "
                "或环境变量 DS_AGENT_DS_READ_SCRIPT 中填写正确路径。"
            )

        window = self.driver.find_window(self._cfg.backend.web.window_titles)
        if window is None:
            raise RuntimeError(
                "未找到浏览器窗口。请确认：\n"
                "  1. 已打开 Firefox\n"
                "  2. 已登录 " + self._cfg.backend.web.url + "\n"
                "  3. 窗口未最小化"
            )
        logger.info("[WEB] 检测到浏览器窗口：%s", window.title)

        try:
            hint = self.reader.check()
            logger.info("[WEB] ds_read.py 检查通过：%s", hint)
        except DsReadError as exc:
            raise RuntimeError(
                "ds_read.py 无法正常工作："
                + str(exc)
                + "\n请手动验证："
                + self._cfg.backend.web.python_executable
                + " "
                + self.reader.script_path
                + " --token-only"
            ) from exc

        if self.session_id:
            logger.info("[WEB] 使用配置会话：%s...", str(self.session_id)[:16])
            self._last_reply_id = self._latest_reply_id()
        else:
            logger.info("[WEB] 会话策略：每个任务可用 Ctrl+J 开新会话")

    def stop(self) -> None:
        try:
            self.driver.close()
        except Exception:
            logger.exception("[WEB] 关闭浏览器驱动失败")

    # ---------- 会话 ----------

    def new_conversation(self) -> None:
        # 请求浏览器打开一个新会话。
        window = self.driver.find_window(self._cfg.backend.web.window_titles)
        if window is None:
            raise RuntimeError("浏览器窗口丢失")
        self.driver.activate(window)
        self.driver.hotkey("ctrl", "j")
        time.sleep(1.5)
        self.session_id = None
        self._last_reply_id = None
        logger.info("[WEB] 已请求新会话")

    # ---------- 主流程 ----------

    def ask(
        self,
        text: str,
        timeout: float | None = None,
        label: str = "消息",
        approval_mgr: Any = None,
        prepend: str = "",
    ) -> str:
        # 发送一条消息，等待稳定回复。
        timeout = float(timeout or self._cfg.loop.reply_timeout)
        actual_text = (prepend + "\n\n" + text) if prepend else text

        if self._cfg.approval.send_to_deepseek and approval_mgr is not None:
            result = approval_mgr.ask_send(actual_text, label=label)
            if not result.approved:
                raise RuntimeError("用户拒绝发送")
            actual_text = result.text
            logger.info("[WEB] 发送内容已确认，%d 字符", len(actual_text))

        self._wait_min_interval()

        prev_id = self._last_reply_id
        is_new_session = self.session_id is None
        t_before_send = time.time()

        logger.info("[WEB] 发送到 DeepSeek...")
        self._send(actual_text, is_new_session=is_new_session)
        self._last_send_time = time.time()

        if is_new_session:
            self._detect_new_session(t_before_send)
            prev_id = None

        reply = self._wait_for_new_reply(prev_id, timeout)
        if not reply:
            raise RuntimeError("等待回复超时（" + str(timeout) + "s）")

        try:
            _, self._last_reply_id = self._read_latest_reply()
        except Exception:
            logger.exception("[WEB] 更新 last_reply_id 失败")

        logger.info("[WEB] 收到回复，%d 字", len(reply))
        return reply

    # ---------- 内部：发送 ----------

    def _send(self, text: str, is_new_session: bool) -> None:
        window = self.driver.find_window(self._cfg.backend.web.window_titles)
        if window is None:
            raise RuntimeError("浏览器窗口丢失，请重新打开浏览器")
        self.driver.activate(window)

        y_ratio = (
            self._cfg.driver.click_ratio_new_session
            if is_new_session
            else self._cfg.driver.click_ratio_existing
        )
        self.driver.click_ratio(window, 0.5, y_ratio)

        self.driver.hotkey("ctrl", "a")
        time.sleep(0.2)
        self.driver.press("delete")
        time.sleep(0.3)

        self.driver.paste(text)
        time.sleep(0.6)
        self.driver.press("enter")

    def _wait_min_interval(self) -> None:
        interval = self._cfg.human.min_interval_between_messages
        elapsed = time.time() - self._last_send_time
        if interval > 0 and elapsed < interval:
            wait = interval - elapsed
            logger.debug("[WEB] 消息间隔等待 %.1fs", wait)
            time.sleep(wait)

    # ---------- 内部：读取回复 ----------

    def _read_latest_reply(self) -> tuple[str, str | None]:
        data = self.reader.read_session_raw(self.session_id)
        return DsReadClient.extract_latest_reply(data)

    def _latest_reply_id(self) -> str | None:
        try:
            _, mid = self._read_latest_reply()
            return mid
        except Exception:
            return None

    def _wait_for_new_reply(self, prev_id: str | None, timeout: float) -> str:
        # 轮询等待新回复。
        # 稳定判定：连续 stable_required 次读到的 (text, mid) 完全一致。
        stable_required = int(self._cfg.loop.stable_required)
        min_wait = float(self._cfg.loop.min_wait)
        poll_interval = float(self._cfg.loop.poll_interval)

        start = time.time()
        deadline = start + timeout

        stable_count = 0
        last_text = ""
        last_mid: str | None = None
        poll_count = 0

        while time.time() < deadline:
            time.sleep(max(0.5, poll_interval))
            poll_count += 1

            try:
                text, mid = self._read_latest_reply()
            except Exception as exc:
                if poll_count <= 3:
                    continue
                logger.debug("[WEB][轮询 %d] 读取异常：%s", poll_count, exc)
                continue

            if poll_count == 1 or poll_count % 5 == 0:
                logger.debug(
                    "[WEB][轮询 %d] mid=%s len=%d",
                    poll_count,
                    mid,
                    len(text or ""),
                )

            if not text or not mid:
                continue
            if prev_id is not None and mid == prev_id:
                continue

            if (time.time() - start) < min_wait:
                stable_count = 0
                last_text = text
                last_mid = mid
                continue

            if text == last_text and mid == last_mid:
                stable_count += 1
                if stable_count >= stable_required:
                    logger.debug(
                        "[WEB][稳定] 连续 %d 次无变化，长度 %d",
                        stable_required,
                        len(text),
                    )
                    return text
            else:
                stable_count = 0
                last_text = text
                last_mid = mid

        logger.warning("[WEB] 等待稳定回复超时，返回最后读到的内容")
        return last_text

    # ---------- 内部：会话探测 ----------

    def _detect_new_session(self, t_before_send: float) -> None:
        logger.info("[WEB] 检测新会话 id...")
        window = 30.0
        for attempt in range(1, 4):
            time.sleep(5 if attempt == 1 else 4)
            try:
                sessions = self.reader.list_sessions(limit=20)
            except DsReadError as exc:
                logger.debug("[WEB] 列会话失败（第 %d 次）：%s", attempt, exc)
                continue
            for s in sessions:
                if s.get("updated_at", 0) >= t_before_send - window:
                    self.session_id = s.get("id") or ""
                    break
            if self.session_id:
                break
        if not self.session_id:
            raise RuntimeError(
                "发送消息后仍无法检测会话 id。\n"
                "请手动运行："
                + self._cfg.backend.web.python_executable
                + " "
                + self.reader.script_path
                + " --list --limit 3"
            )
        logger.info("[WEB] 会话 id：%s...", str(self.session_id)[:16])
