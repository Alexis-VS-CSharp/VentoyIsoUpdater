"""
Batocera — Retrogaming OS.
Source : https://mirrors.o2switch.fr/batocera/x86_64/stable/last/

updates.batocera.org (utilisé auparavant) est un frontal incohérent : il
redirige correctement vers ce miroir pour l'image elle-même mais renvoie
404 pour son sidecar .md5 — on interroge donc directement le miroir, dont
le listing donne toujours le nom du build courant.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_MIRROR_URL = "https://mirrors.o2switch.fr/batocera/x86_64/stable/last/"


def _fetch_bare_md5(url: str) -> Optional[str]:
    """Le sidecar .md5 de Batocera ne contient que l'empreinte, sans nom de
    fichier — pas le format GNU coreutils habituel."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None
    m = re.match(r"^([0-9a-fA-F]{32})\s*$", resp.text.strip())
    return m.group(1).lower() if m else None


class BatoceraChecker(BaseChecker):
    MIRROR_URL = _MIRROR_URL

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.MIRROR_URL, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            m = re.search(r'href="(batocera-x86_64-([\d.]+-\d+)\.img\.gz)"', resp.text)
            if not m:
                return []
            filename, version = m.group(1), m.group(2)
            checksum = _fetch_bare_md5(self.MIRROR_URL + filename + ".md5")
            return [VersionInfo(
                version=version,
                download_url=self.MIRROR_URL + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="md5",
                variant_label="x86_64",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"batocera-x86_64-([\d.]+-\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None
