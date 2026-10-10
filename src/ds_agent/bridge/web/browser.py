# 浏览器驱动抽象与实现。
#
# 唯一允许 import pyautogui / pyperclip / pygetwindow 的地方。
# 其它驱动（Playwright / CDP）可在此扩展，不污染上层逻辑。
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


@dataclass
class WindowInfo:
    # 窗口几何信息的简化表示，便于跨驱动传递。
    handle: Any
    title: str
    left: int
    top: int
    width: int
    height: int


@runtime_checkable
class BrowserDriver(Protocol):
    # 浏览器驱动接口。所有实现都必须满足该协议。

    def find_window(self, titles: list[str]) -> WindowInfo | None:
        # 按标题列表查找第一个匹配窗口。
        ...

    def activate(self, window: WindowInfo) -> None:
        # 把窗口激活到前台。
        ...

    def click_ratio(self, window: WindowInfo, x_ratio: float, y_ratio: float) -> None:
        # 在窗口内容区按比例点击。
        ...

    def paste(self, text: str) -> None:
        # 通过剪贴板把文本粘贴到当前焦点。
        ...

    def press(self, key: str) -> None:
        # 按下单个按键。
        ...

    def hotkey(self, *keys: str) -> None:
        # 按下组合键。
        ...

    def close(self) -> None:
        # 释放资源。
        ...


def _random_sleep(lo: float, hi: float) -> None:
    if hi <= lo:
        time.sleep(max(0.0, lo))
        return
    time.sleep(random.uniform(lo, hi))


class PyAutoGUIDriver:
    # 基于 PyAutoGUI / Pyperclip / PyGetWindow 的默认驱动。
    #
    # 延迟到 __init__ 才导入 GUI 依赖，方便在无 GUI 环境下 import 本模块。

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        try:
            import pyautogui
            import pygetwindow as gw
            import pyperclip
        except ImportError as exc:
            raise RuntimeError(
                "缺少 GUI 依赖：" + str(exc) + "。请安装： "
                "pip install pyautogui pyperclip pygetwindow"
            ) from exc
        pyautogui.PAUSE = 0.05
        self._pg = pyautogui
        self._gw = gw
        self._clip = pyperclip

    def find_window(self, titles: list[str]) -> WindowInfo | None:
        for title in titles:
            try:
                windows = self._gw.getWindowsWithTitle(title)
            except Exception as exc:
                logger.debug("查找窗口 %s 失败：%s", title, exc)
                continue
            for win in windows:
                try:
                    return WindowInfo(
                        handle=win,
                        title=win.title,
                        left=win.left,
                        top=win.top,
                        width=win.width,
                        height=win.height,
                    )
                except Exception:
                    continue
        return None

    def activate(self, window: WindowInfo) -> None:
        win = window.handle
        try:
            if getattr(win, "isMinimized", False):
                win.restore()
                time.sleep(0.5)
        except Exception:
            pass
        try:
            win.activate()
        except Exception:
            offset = self._cfg.driver.activate_retry_click_offset
            try:
                self._pg.click(window.left + offset, window.top + 15)
            except Exception as exc:
                logger.debug("激活窗口失败：%s", exc)
        _random_sleep(0.8, 1.2)

    def click_ratio(self, window: WindowInfo, x_ratio: float, y_ratio: float) -> None:
        content_left = window.left + 4
        content_top = window.top + 32
        content_width = max(1, window.width - 8)
        content_height = max(1, window.height - 36)
        x = content_left + int(content_width * x_ratio)
        y = content_top + int(content_height * y_ratio)
        self._pg.click(x, y)
        _random_sleep(0.5, 0.9)

    def paste(self, text: str) -> None:
        self._clip.copy(text)
        _random_sleep(0.3, 0.6)
        self._pg.hotkey("ctrl", "v")
        _random_sleep(0.8, 1.5)

    def press(self, key: str) -> None:
        self._pg.press(key)

    def hotkey(self, *keys: str) -> None:
        self._pg.hotkey(*keys)

    def close(self) -> None:
        return None


class PlaywrightDriver:
    # Playwright 驱动占位实现。
    #
    # 规划要点：需要用户在首次运行时手动登录一次并保存 storage state。
    # 保留占位以明确扩展点，避免在未安装 playwright 时污染启动路径。

    def __init__(self, cfg: AppConfig) -> None:
        raise RuntimeError(
            "Playwright 驱动尚未实现。请安装 playwright 后在本模块扩展，"
            "或先使用 driver.type=pyautogui。"
        )


class CDPDriver:
    # Chrome DevTools Protocol 驱动占位实现。

    def __init__(self, cfg: AppConfig) -> None:
        raise RuntimeError("CDP 驱动尚未实现。请先使用 driver.type=pyautogui。")


_DRIVERS = {
    "pyautogui": PyAutoGUIDriver,
    "playwright": PlaywrightDriver,
    "cdp": CDPDriver,
}


def create_driver(cfg: AppConfig) -> BrowserDriver:
    # 按配置创建驱动实例。
    kind = (cfg.driver.type or "pyautogui").strip().lower()
    cls = _DRIVERS.get(kind)
    if cls is None:
        raise RuntimeError("未知驱动类型：" + kind + "。可选：" + ", ".join(_DRIVERS))
    logger.debug("创建浏览器驱动：%s", kind)
    return cls(cfg)
