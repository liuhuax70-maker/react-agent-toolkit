"""日志配置。"""
from __future__ import annotations

import logging

from app.config import get_settings

_FORMAT = "%(asctime)s %(levelname)-5s %(name)s | %(message)s"


def setup_logging() -> None:
    level = getattr(logging, get_settings().log_level, logging.INFO)
    logging.basicConfig(level=level, format=_FORMAT, datefmt="%H:%M:%S")
