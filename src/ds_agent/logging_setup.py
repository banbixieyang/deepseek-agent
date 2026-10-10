# 日志配置。
#
# 统一使用 logging，替代散落的 print 与 traceback.print_exc()。
from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from ds_agent.config import ensure_directories, resolve_path
from ds_agent.schema import AppConfig

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_NAME = "ds_agent"


def _resolve_level(name: str) -> int:
    return getattr(logging, str(name).upper(), logging.INFO)


def setup_logging(cfg: AppConfig, name: str = _DEFAULT_NAME) -> logging.Logger:
    # 配置并返回指定名称的 logger。
    #
    # 控制台始终输出；cfg.logging.to_file 为真时额外写入按天轮转的文件。
    logger = logging.getLogger(name)
    level = _resolve_level(cfg.logging.level)
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    formatter = logging.Formatter(_FORMAT, _DATEFMT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)
    logger.addHandler(console)

    if cfg.logging.to_file:
        ensure_directories(cfg)
        log_dir = resolve_path(cfg.paths.log_dir)
        file_handler = TimedRotatingFileHandler(
            log_dir / "ds_agent.log",
            when="midnight",
            backupCount=max(1, int(cfg.logging.keep_days)),
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    # 获取 logger。未显式配置时沿用父 logger 设置。
    return logging.getLogger(name or _DEFAULT_NAME)
