"""
Gestion des téléchargements avec progression et vérification de checksum.
"""

import os
import hashlib
import threading
from typing import Callable, Optional

import requests


class DownloadError(Exception):
    pass


def download_file(
    url: str,
    dest_path: str,
    on_progress: Optional[Callable[[int, int], None]] = None,
    checksum: Optional[str] = None,
    checksum_type: str = "sha256",
    chunk_size: int = 1024 * 1024,  # 1 MB
    cancel_event: Optional[threading.Event] = None,
) -> str:
    """
    Télécharge un fichier vers dest_path.

    Args:
        url: URL source
        dest_path: chemin de destination (fichier complet)
        on_progress: callback(bytes_downloaded, total_bytes) appelé à chaque chunk
        checksum: hash attendu (optionnel)
        checksum_type: 'sha256' ou 'md5'
        chunk_size: taille des blocs
        cancel_event: threading.Event pour annuler le téléchargement

    Returns:
        Chemin du fichier téléchargé

    Raises:
        DownloadError en cas d'échec ou d'annulation
    """
    tmp_path = dest_path + ".part"

    try:
        with requests.get(url, stream=True, timeout=30) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0

            hasher = hashlib.new(checksum_type) if checksum else None

            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if cancel_event and cancel_event.is_set():
                        raise DownloadError("Téléchargement annulé")
                    if chunk:
                        f.write(chunk)
                        if hasher:
                            hasher.update(chunk)
                        downloaded += len(chunk)
                        if on_progress:
                            on_progress(downloaded, total)

        # Vérification du checksum
        if checksum and hasher:
            computed = hasher.hexdigest()
            if computed.lower() != checksum.lower():
                os.remove(tmp_path)
                raise DownloadError(
                    f"Checksum invalide : attendu {checksum}, obtenu {computed}"
                )

        # Renommage atomique (os.replace est atomique sur Linux, sûr sur Windows)
        os.replace(tmp_path, dest_path)
        return dest_path

    except DownloadError:
        raise
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise DownloadError(f"Erreur téléchargement : {e}") from e


def download_logo(
    url: str,
    dest_path: str,
    size: tuple[int, int] = (128, 128),
) -> tuple[bool, Optional[str]]:
    """
    Télécharge (ou copie) un logo et le convertit en PNG redimensionné.

    Préfixe spécial ``local:<filename>`` : copie depuis assets/logos/ du projet
    au lieu de télécharger depuis internet.

    Retourne (True, None) en cas de succès, (False, "raison") en cas d'échec.
    """
    try:
        from PIL import Image
        import io

        _MAX_LOGO_BYTES = 5 * 1024 * 1024  # 5 MB

        if url.startswith("local:"):
            # Fichier embarqué dans assets/logos/ du projet
            filename = url[len("local:"):]
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "logos")
            # Rejette toute tentative de traversée de chemin (ex: "local:../../etc/passwd") :
            # filename doit désigner un fichier directement dans assets_dir, sans séparateur.
            if not filename or "/" in filename or "\\" in filename or filename in (".", ".."):
                return False, "Nom de fichier local invalide"
            src = os.path.join(assets_dir, filename)
            if os.path.realpath(src) != os.path.join(os.path.realpath(assets_dir), filename):
                return False, "Nom de fichier local invalide"
            if not os.path.isfile(src):
                return False, f"Fichier local introuvable : {filename}"
            if os.path.getsize(src) > _MAX_LOGO_BYTES:
                return False, "Logo local trop volumineux (> 5 MB)"
            img = Image.open(src).convert("RGBA")
        else:
            resp = requests.get(url, stream=True, timeout=10)
            resp.raise_for_status()
            # Lit avec limite de taille pour éviter une saturation mémoire
            data = b""
            for chunk in resp.iter_content(chunk_size=65536):
                data += chunk
                if len(data) > _MAX_LOGO_BYTES:
                    return False, "Logo trop volumineux (> 5 MB)"
            img = Image.open(io.BytesIO(data)).convert("RGBA")

        img = img.resize(size, Image.LANCZOS)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        img.save(dest_path, "PNG")
        return True, None

    except requests.HTTPError as e:
        return False, f"HTTP {e.response.status_code if e.response else '?'}"
    except requests.ConnectionError:
        return False, "Connexion impossible"
    except requests.Timeout:
        return False, "Délai d'attente dépassé"
    except Exception as e:
        return False, str(e)[:80]
