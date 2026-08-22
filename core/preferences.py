"""
Persistent application preferences.
Stored in ~/.config/ventoyisoupdater/prefs.json
"""

import json
import os
from pathlib import Path

_PREFS_DIR = Path.home() / ".config" / "ventoyisoupdater"
_PREFS_FILE = _PREFS_DIR / "prefs.json"

_DEFAULTS: dict = {
    "download_folder": "",          # default download folder (empty = Ventoy drive)
    "stable_only": True,            # filter to stable versions only
    "check_on_startup": False,      # check for updates on startup
    "last_drive": "",               # last selected mount point
    "window_geometry": "",          # main window geometry
    "language": "fr",               # UI language: "fr" or "en"
}


def load() -> dict:
    """Loads preferences from the file. Returns the defaults if absent."""
    try:
        with open(_PREFS_FILE, encoding="utf-8") as f:
            stored = json.load(f)
        prefs = dict(_DEFAULTS)
        prefs.update({k: v for k, v in stored.items() if k in _DEFAULTS})
        return prefs
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULTS)


def save(prefs: dict) -> None:
    """Saves preferences to the file."""
    try:
        _PREFS_DIR.mkdir(parents=True, exist_ok=True)
        with open(_PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def get(key: str):
    """Shortcut: reads a single key."""
    return load().get(key, _DEFAULTS.get(key))


def set_key(key: str, value) -> None:
    """Shortcut: updates a single key and saves."""
    if key not in _DEFAULTS:
        return
    prefs = load()
    prefs[key] = value
    save(prefs)
