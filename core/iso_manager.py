"""
Opérations sur les fichiers ISO : téléchargement, suppression.
Les ISO ne sont jamais remplacées automatiquement — plusieurs versions coexistent.
"""

import os
import shutil
from typing import Optional


def get_download_path(dest_folder: str, filename: str) -> str:
    """
    Retourne le chemin de destination pour un téléchargement dans dest_folder.
    Crée le dossier si nécessaire.
    Si un fichier du même nom existe déjà, ajoute un suffixe numérique.

    ``filename`` provient de VersionInfo, dont la valeur est extraite par les
    vérificateurs de sources/ depuis des pages/API distantes (regex sur du
    HTML ou du JSON) — on ne lui fait donc pas confiance aveuglément.
    ``os.path.basename`` neutralise toute tentative de traversée de chemin
    (``../../etc/...`` ou chemin absolu) avant de le joindre à dest_folder.
    """
    filename = os.path.basename(filename)
    if not filename or filename in (".", ".."):
        raise ValueError(f"Nom de fichier invalide : {filename!r}")
    dest_folder = os.path.realpath(dest_folder)
    os.makedirs(dest_folder, exist_ok=True)
    path = os.path.join(dest_folder, filename)
    if not os.path.exists(path):
        return path
    # Fichier déjà présent → suffixe pour ne pas écraser
    base, ext = os.path.splitext(filename)
    MAX_SUFFIX = 999
    for i in range(1, MAX_SUFFIX + 1):
        candidate = os.path.join(dest_folder, f"{base}_{i}{ext}")
        if not os.path.exists(candidate):
            return candidate
    raise OSError(f"Impossible de trouver un nom libre pour {filename} dans {dest_folder}")


# Correspondance catégorie → nom de dossier candidat sur la clé
_CATEGORY_FOLDERS = {
    "linux":    ["linux", "Linux"],
    "gaming":   ["gaming", "Gaming", "linux", "Linux"],
    "server":   ["server", "Server", "linux", "Linux"],
    "security": ["security", "Security", "linux", "Linux"],
    "bsd":      ["bsd", "BSD", "linux", "Linux"],
    "windows":  ["windows", "Windows"],
}


def suggest_dest_folder(mount_point: str, distro_cfg: dict, iso_entries: list) -> str:
    """
    Retourne le dossier de destination suggéré pour télécharger une nouvelle ISO.

    Priorité :
    1. Un dossier déjà utilisé par des ISO de cette distro sur la clé
    2. Le dossier de catégorie existant + sous-dossier nommé d'après la distro
    3. Sous-dossier nommé d'après la distro à la racine
    """
    distro_id = distro_cfg.get("id", "")
    distro_name = distro_cfg.get("name", distro_id)
    category = distro_cfg.get("category", "linux")

    # 1. Cherche un dossier existant pour cette distro parmi les ISO déjà présentes
    for entry in iso_entries:
        if entry.distro_id == distro_id and entry.folder and entry.folder != "/":
            candidate = os.path.join(mount_point, entry.folder.lstrip("/"))
            if os.path.isdir(candidate):
                return candidate

    # 2. Cherche un dossier de catégorie existant, crée un sous-dossier distro dedans
    for folder_name in _CATEGORY_FOLDERS.get(category, ["linux"]):
        cat_dir = os.path.join(mount_point, folder_name)
        if os.path.isdir(cat_dir):
            return os.path.join(cat_dir, distro_name)

    # 3. Fallback : sous-dossier à la racine de la clé
    return os.path.join(mount_point, distro_name)


def delete_iso(path: str) -> bool:
    """Supprime une ISO. Retourne True si réussi."""
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def get_free_space(path: str) -> int:
    """Retourne l'espace disque libre en octets pour le chemin donné."""
    return shutil.disk_usage(path).free


def list_isos_in_folder(folder: str) -> list[str]:
    """Liste toutes les ISO dans un dossier (non récursif)."""
    try:
        return [
            f for f in os.listdir(folder)
            if f.lower().endswith(".iso")
        ]
    except OSError:
        return []
