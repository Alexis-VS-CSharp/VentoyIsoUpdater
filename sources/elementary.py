"""
Vérificateur de version pour elementary OS.
Source : https://elementary.io/ — les releases GitHub (elementary/os)
n'ont plus aucun asset ISO attaché (distribution "pay what you want" via
leur propre site), le lien réel est sur la page d'accueil elle-même.
Aucune empreinte n'est publiée par le projet à ce jour.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_HOMEPAGE = "https://elementary.io/"


class ElementaryChecker(BaseChecker):
    HOMEPAGE = _HOMEPAGE

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.HOMEPAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            m = re.search(
                r'href="(?://|https://)?(ams\d*\.dl\.elementary\.io/download/[^"]+'
                r'(elementaryos-([\d.]+)-stable-amd64\.[\d]+\.iso))"',
                resp.text
            )
            if not m:
                return []
            path, filename, version = m.group(1), m.group(2), m.group(3)
            url = "https://" + path
            return [VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                variant_label="amd64",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"elementaryos-(\d+\.\d+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None
