"""
Vérificateur de version pour GParted Live.
Téléchargement : SourceForge project gparted/files/gparted-live-stable/
Version + empreinte : https://gparted.org/gparted-live/stable/CHECKSUMS.TXT

Ce fichier officiel (pas sur SourceForge) contient déjà le nom exact du
fichier ISO courant dans sa section SHA256SUMS — on en tire la version et
l'empreinte en un seul appel, sans jamais avoir besoin de lister le
répertoire SourceForge (qui bloque parfois les requêtes automatisées).
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_SF_URL = "https://sourceforge.net/projects/gparted/files/gparted-live-stable/"
_CHECKSUMS_URL = "https://gparted.org/gparted-live/stable/CHECKSUMS.TXT"


class GPartedChecker(BaseChecker):
    SF_URL = _SF_URL
    CHECKSUMS_URL = _CHECKSUMS_URL

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.CHECKSUMS_URL, timeout=10)
            resp.raise_for_status()
            # Isole la section SHA256SUMS pour ne pas capturer le MD5/SHA1
            # (mêmes noms de fichiers, empreintes de longueurs différentes)
            section = resp.text.split("SHA256SUMS:")[-1]
            m = re.search(
                r"([0-9a-fA-F]{64})\s+(gparted-live-([\d.]+-\d+)-amd64\.iso)",
                section
            )
            if not m:
                return []
            checksum, filename, version = m.group(1), m.group(2), m.group(3)
            dl_url = f"{self.SF_URL}{version}/{filename}/download"
            return [VersionInfo(
                version=version,
                download_url=dl_url,
                filename=filename,
                checksum=checksum.lower(),
                checksum_type="sha256",
                variant_label="amd64",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"gparted-live-([\d.]+-\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None
