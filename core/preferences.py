"""
Préférences persistantes de l'application.
Stockées dans ~/.config/ventoyisoupdater/prefs.json
"""

import json
import os
from pathlib import Path

_PREFS_DIR = Path.home() / ".config" / "ventoyisoupdater"
_PREFS_FILE = _PREFS_DIR / "prefs.json"

_DEFAULTS: dict = {
    "download_folder": "",          # dossier de téléchargement par défaut (vide = clé Ventoy)
    "stable_only": True,            # filtre versions stables uniquement
    "check_on_startup": False,      # vérifier les mises à jour au démarrage
    "last_drive": "",               # dernier point de montage sélectionné
    "window_geometry": "",          # géométrie de la fenêtre principale
    "language": "fr",               # langue de l'interface : "fr" ou "en"
}


def load() -> dict:
    """Charge les préférences depuis le fichier. Retourne les valeurs par défaut si absent."""
    try:
        with open(_PREFS_FILE, encoding="utf-8") as f:
            stored = json.load(f)
        prefs = dict(_DEFAULTS)
        prefs.update({k: v for k, v in stored.items() if k in _DEFAULTS})
        return prefs
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(_DEFAULTS)


def save(prefs: dict) -> None:
    """Sauvegarde les préférences dans le fichier."""
    try:
        _PREFS_DIR.mkdir(parents=True, exist_ok=True)
        with open(_PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2, ensure_ascii=False)
    except OSError:
        pass


def get(key: str):
    """Raccourci : lit une seule clé."""
    return load().get(key, _DEFAULTS.get(key))


def set_key(key: str, value) -> None:
    """Raccourci : met à jour une seule clé et sauvegarde."""
    if key not in _DEFAULTS:
        return
    prefs = load()
    prefs[key] = value
    save(prefs)
