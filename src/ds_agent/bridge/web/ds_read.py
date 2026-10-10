# 外部 ds_read.py 的封装。
#
# 说明：ds_read.py 不在本项目内，需要用户自行获取并配置路径。
# 本模块只负责调用它、解析 JSON、给出可读错误。
from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from ds_agent.logging_setup import get_logger
from ds_agent.schema import AppConfig

logger = get_logger(__name__)


class DsReadError(RuntimeError):
    # ds_read.py 调用失败时抛出。
    pass


def _build_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


class DsReadClient:
    # 调用外部 ds_read.py 的客户端。

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._script = (cfg.backend.web.ds_read_script or "").strip()
        self._python = cfg.backend.web.python_executable or "python"
        self._env = _build_env()

    @property
    def script_path(self) -> str:
        return self._script

    def is_configured(self) -> bool:
        # 路径非空且文件存在时返回 True。
        return bool(self._script) and os.path.isfile(self._script)

    def _run(self, args: list[str], timeout: float) -> str:
        if not self.is_configured():
            raise DsReadError(
                "ds_read.py 未配置或不存在："
                + (self._script or "(空)")
                + "。请在 config/config.yaml 的 backend.web.ds_read_script "
                "或环境变量 DS_AGENT_DS_READ_SCRIPT 中填写正确路径。"
            )
        cmd = [self._python, self._script, *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=self._env,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise DsReadError(
                "找不到解释器：" + self._python + "。请修改 backend.web.python_executable。"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise DsReadError("ds_read.py 调用超时（" + str(timeout) + "s）") from exc

        if result.returncode != 0:
            raise DsReadError(
                "ds_read.py 返回码 "
                + str(result.returncode)
                + "\nstdout: "
                + (result.stdout or "")[:500]
                + "\nstderr: "
                + (result.stderr or "")[:500]
            )
        return result.stdout or ""

    def check(self, timeout: float = 60.0) -> str:
        # 快速健康检查。成功时返回 ds_read.py 的提示行。
        out = self._run(["--token-only"], timeout=timeout)
        if "[+]" not in out:
            raise DsReadError("ds_read.py 输出异常：" + out[:300])
        return out.strip()

    def read_session_raw(self, session_id: str | None, timeout: float = 120.0) -> dict[str, Any]:
        # 读取某个会话（或最新会话）的原始 JSON。
        args = ["--session", session_id, "--raw"] if session_id else ["--latest", "--raw"]
        out = self._run(args, timeout=timeout)
        if not out.strip():
            raise DsReadError("ds_read.py 无输出")
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            raise DsReadError(
                "ds_read.py 输出不是合法 JSON：" + str(exc) + "\n前 200 字：" + out[:200]
            ) from exc
        if not isinstance(data, dict):
            raise DsReadError("ds_read.py 返回结构不是对象")
        return data

    def list_sessions(self, limit: int = 20, timeout: float = 60.0) -> list[dict[str, Any]]:
        # 列出最近会话，按 updated_at 降序。
        out = self._run(["--list", "--limit", str(limit), "--raw"], timeout=timeout)
        if not out.strip():
            raise DsReadError("ds_read.py 无输出（--list）")
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            raise DsReadError(
                "ds_read.py --list 输出不是合法 JSON：" + str(exc) + "\n前 200 字：" + out[:200]
            ) from exc
        if not isinstance(data, list):
            raise DsReadError("ds_read.py --list 返回结构不是数组")
        return sorted(data, key=lambda s: s.get("updated_at", 0), reverse=True)

    @staticmethod
    def extract_latest_reply(data: dict[str, Any]) -> tuple[str, str | None]:
        # 从原始 JSON 中提取最新一条 RESPONSE 消息。
        # 返回 (内容, message_id)，找不到时返回 ("", None)。
        session = data.get("chat_session") or {}
        messages = data.get("chat_messages") or []
        if not isinstance(messages, list) or not messages:
            return "", None

        by_id = {m.get("message_id"): m for m in messages if isinstance(m, dict)}
        chain = DsReadClient._active_chain(session, by_id) or messages

        for msg in reversed(chain):
            for fr in msg.get("fragments") or []:
                if not isinstance(fr, dict):
                    continue
                if fr.get("type") == "RESPONSE":
                    content = (fr.get("content") or "").strip()
                    if content:
                        return content, msg.get("message_id")
        return "", None

    @staticmethod
    def _active_chain(
        session: dict[str, Any], by_id: dict[Any, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        cur = session.get("current_message_id")
        chain: list[dict[str, Any]] = []
        seen: set = set()
        guard = 0
        while cur and cur in by_id and cur not in seen and guard < 20000:
            seen.add(cur)
            chain.append(by_id[cur])
            cur = by_id[cur].get("parent_id")
            guard += 1
        chain.reverse()
        return chain
