"""
Tails OS — Privacy/anonymity OS. Source : tails.net

Le téléchargement passe par download.tails.net, qui redirige (302) vers un
miroir réel — l'ancien chemin "tails.net/torrents/files/<fichier>" utilisé
ici pointait vers une page HTML (répertoire), pas le fichier lui-même.

Tails ne publie pas d'empreinte en clair (SHA256SUMS/.sha256) : seule une
signature OpenPGP (.sig) accompagne l'ISO. Ce projet ne vérifie pas les
signatures OpenPGP (voir core/downloader.py) — `manual_verify_url` est donc
renseigné pour que l'interface invite l'utilisateur à vérifier lui-même via
la procédure officielle, plutôt que de télécharger sans aucune indication.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_MANUAL_VERIFY_URL = "https://tails.net/install/linux/index.fr.html"


class TailsChecker(BaseChecker):
    DOWNLOAD_URL = "https://tails.net/install/download/"
    DOWNLOAD_BASE = "https://download.tails.net/tails/stable/"
    # API JSON de mise à jour
    RELEASES_APIS = [
        "https://tails.net/update/v2/Tails/i386/stable/latest.json",
        "https://tails.net/update/v2/Tails/amd64/stable/latest.json",
    ]

    def _version_info(self, version: str) -> VersionInfo:
        filename = f"tails-amd64-{version}.iso"
        return VersionInfo(
            version=version,
            download_url=f"{self.DOWNLOAD_BASE}tails-amd64-{version}/{filename}",
            filename=filename,
            release_notes_url=f"https://tails.net/news/version_{version.replace('.', '_')}/",
            variant_label="Live USB",
            manual_verify_url=_MANUAL_VERIFY_URL,
        )

    def get_latest_version(self) -> Optional[VersionInfo]:
        # Essai 1 : API JSON
        for api_url in self.RELEASES_APIS:
            try:
                resp = requests.get(api_url, timeout=10)
                resp.raise_for_status()
                version = resp.json().get("version", "")
                if version:
                    return self._version_info(version)
            except Exception as _exc:
                logger.debug("%s: échec ignoré : %s", __name__, _exc)
                continue

        # Essai 2 : scrape la page de téléchargement
        try:
            resp = requests.get(
                self.DOWNLOAD_URL,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            m = re.search(r"tails-amd64-([\d.]+)\.(?:iso|img)", resp.text)
            if m:
                return self._version_info(m.group(1))
            versions = re.findall(r"Tails[\s_-]+([\d.]+)", resp.text)
            if versions:
                return self._version_info(sorted(set(versions), reverse=True)[0])
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)

        return None

    def get_all_versions(self) -> list[VersionInfo]:
        latest = self.get_latest_version()
        return [latest] if latest else []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"tails(?:-amd64)?-(\d+\.\d+(?:\.\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None
