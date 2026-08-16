"""
Gestion des logos de distro pour le thème Ventoy existant.

Logique :
- Les logos sont nommés d'après le `grub_class` de la distro (= nom de classe GRUB)
  ex : grub_class="Zorin" → fichier "Zorin.png" dans icons/
- ventoy.json contient des `menu_class` qui mappent dossiers → classes GRUB
- Quand on ajoute un nouveau logo, on propose aussi d'ajouter l'entrée menu_class
  correspondante dans ventoy.json
"""

import os
import json
import shutil
from typing import Callable, Optional

from core.downloader import download_logo


# ── Lecture / écriture de ventoy.json ────────────────────────────────────────

def load_ventoy_json(ventoy_json_path: str) -> dict:
    """Charge ventoy.json. Retourne {} si absent ou illisible."""
    try:
        with open(ventoy_json_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ventoy_json(ventoy_json_path: str, data: dict) -> bool:
    """Sauvegarde ventoy.json avec une indentation propre. Retourne True si ok."""
    backup = ventoy_json_path + ".bak"
    backup_created = False
    if os.path.isfile(ventoy_json_path):
        try:
            shutil.copy2(ventoy_json_path, backup)
            backup_created = True
        except Exception:
            pass  # Pas de backup disponible, on continue quand même
    try:
        with open(ventoy_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        # Restaure le backup en cas d'échec d'écriture
        if backup_created:
            try:
                shutil.copy2(backup, ventoy_json_path)
            except Exception:
                pass  # Impossible de restaurer : ventoy.json peut être corrompu
        return False


def get_existing_menu_classes(ventoy_json_path: str) -> dict[str, str]:
    """
    Retourne un dict {pattern → class} depuis les menu_class de ventoy.json.
    pattern est soit "dir" soit "parent".
    """
    data = load_ventoy_json(ventoy_json_path)
    result = {}
    for entry in data.get("menu_class", []):
        key = entry.get("dir") or entry.get("parent", "")
        cls = entry.get("class", "")
        if key and cls:
            result[key] = cls
    return result


def add_menu_class_entry(
    ventoy_json_path: str,
    iso_folder: str,
    grub_class: str,
) -> bool:
    """
    Ajoute une entrée menu_class dans ventoy.json pour associer iso_folder → grub_class.
    Ne fait rien si l'entrée existe déjà pour ce dossier.
    Retourne True si une entrée a été ajoutée.
    """
    if not ventoy_json_path or not os.path.isfile(ventoy_json_path):
        return False

    data = load_ventoy_json(ventoy_json_path)
    menu_class = data.get("menu_class", [])

    # Normalise le chemin : doit commencer par /
    folder = "/" + iso_folder.lstrip("/\\").replace("\\", "/")

    # Vérifie si ce dossier est déjà mappé
    for entry in menu_class:
        if entry.get("dir") == folder:
            return False  # déjà présent

    # Insère avant la règle générique /Linux (si elle existe)
    new_entry = {"dir": folder, "class": grub_class}
    insert_pos = len(menu_class)
    for i, entry in enumerate(menu_class):
        # La règle générique (/Linux, /) doit rester en dernier
        d = entry.get("dir", "")
        if d in ("/Linux", "/", "/Server") and d != folder:
            insert_pos = i
            break
    menu_class.insert(insert_pos, new_entry)
    data["menu_class"] = menu_class
    return save_ventoy_json(ventoy_json_path, data)


# ── Gestion des logos ─────────────────────────────────────────────────────────

def sync_logos(
    icons_dir: str,
    distros_db: dict,
    iso_entries: list,
    force: bool = False,
    ventoy_json_path: Optional[str] = None,
    on_progress: Optional[Callable] = None,
) -> dict[str, dict]:
    """
    Télécharge les logos manquants pour toutes les distros des ISO détectées.

    - Le nom du fichier = grub_class + ".png" (ex: "Zorin.png", "ubuntu.png")
    - Si ventoy_json_path fourni, propose aussi d'ajouter les entrées menu_class
      manquantes dans ventoy.json

    Retourne {logo_filename: {"success": bool, "name": str, "error": str|None, "skipped": bool}}
    """
    if not os.path.isdir(icons_dir):
        return {}

    # Collecte les classes uniques des ISO présentes sur la clé
    # On group par grub_class → (logo_url, list of iso folders)
    needed: dict[str, dict] = {}
    for entry in iso_entries:
        if not entry.distro_id:
            continue
        distro_cfg = next(
            (d for d in distros_db.get("distros", []) if d["id"] == entry.distro_id),
            None
        )
        if not distro_cfg:
            continue
        grub_class = distro_cfg.get("grub_class")
        logo_url   = distro_cfg.get("logo_url")
        if not grub_class or not logo_url:
            continue
        if grub_class not in needed:
            needed[grub_class] = {
                "logo_url": logo_url,
                "name": distro_cfg["name"],
                "folders": set(),
            }
        # Collecte les dossiers pour la mise à jour de menu_class
        if entry.folder and entry.folder != "/":
            needed[grub_class]["folders"].add(entry.folder)

    results: dict[str, dict] = {}
    existing_classes = get_existing_menu_classes(ventoy_json_path) if ventoy_json_path else {}

    for grub_class, info in needed.items():
        logo_filename = grub_class + ".png"
        dest_path = os.path.join(icons_dir, logo_filename)

        # Déjà présent et pas de forçage : on considère OK sans retélécharger
        if os.path.exists(dest_path) and not force:
            results[logo_filename] = {
                "success": True,
                "name": info["name"],
                "error": None,
                "skipped": True,
            }
        else:
            ok, err = download_logo(
                url=info["logo_url"],
                dest_path=dest_path,
                size=(128, 128),
            )
            results[logo_filename] = {
                "success": ok,
                "name": info["name"],
                "error": err,
                "skipped": False,
            }

        success = results[logo_filename]["success"]

        # Mise à jour ventoy.json si demandé et logo OK
        if ventoy_json_path and success:
            class_values = set(existing_classes.values())
            if grub_class not in class_values:
                # Ajoute une entrée par dossier d'ISO
                for folder in info["folders"]:
                    add_menu_class_entry(ventoy_json_path, folder, grub_class)
                # Recharge les classes après update
                existing_classes = get_existing_menu_classes(ventoy_json_path)

        if on_progress:
            on_progress(info["name"], success)

    return results


def get_missing_logos(icons_dir: str, iso_entries: list, distros_db: dict) -> list[str]:
    """
    Retourne la liste des logos (grub_class.png) manquants dans icons/
    pour les ISO présentes sur la clé.
    """
    if not os.path.isdir(icons_dir):
        return []

    missing = []
    seen = set()
    for entry in iso_entries:
        distro_cfg = next(
            (d for d in distros_db.get("distros", []) if d["id"] == entry.distro_id),
            None
        ) if entry.distro_id else None
        if not distro_cfg:
            continue
        grub_class = distro_cfg.get("grub_class")
        if not grub_class or grub_class in seen:
            continue
        seen.add(grub_class)
        logo_file = grub_class + ".png"
        if not os.path.exists(os.path.join(icons_dir, logo_file)):
            missing.append(logo_file)
    return missing


def get_unmatched_isos(
    iso_entries: list,
    ventoy_json_path: str,
) -> list:
    """
    Retourne les IsoEntry dont le dossier n'est couvert par aucune règle menu_class.
    Utile pour signaler à l'utilisateur ce qui n'a pas d'icône.
    """
    if not ventoy_json_path:
        return []
    existing = get_existing_menu_classes(ventoy_json_path)

    unmatched = []
    for entry in iso_entries:
        folder = "/" + entry.folder.lstrip("/\\").replace("\\", "/")
        matched = False
        for pattern in existing:
            if folder == pattern or folder.startswith(pattern + "/") or folder.startswith(pattern):
                matched = True
                break
        if not matched:
            unmatched.append(entry)
    return unmatched
