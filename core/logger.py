"""
Logging centralisé de l'application.
Fichier de log : ~/.config/ventoyisoupdater/ventoyisoupdater.log
"""

import logging
import os
from pathlib import Path

_LOG_DIR  = Path.home() / ".config" / "ventoyisoupdater"
_LOG_FILE = _LOG_DIR / "ventoyisoupdater.log"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB par fichier

def _setup() -> logging.Logger:
    log = logging.getLogger("ventoyisoupdater")
    if log.handlers:
        return log
    log.setLevel(logging.DEBUG)
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            _LOG_FILE, maxBytes=_MAX_BYTES, backupCount=3, encoding="utf-8"
        )
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh.setFormatter(fmt)
        log.addHandler(fh)
    except Exception:
        pass
    # Warnings+ also go to stderr
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    log.addHandler(ch)
    return log


logger = _setup()
