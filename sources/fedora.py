"""
Vérificateur de version pour Fedora (Workstation et Server).
Source : https://dl.fedoraproject.org/pub/fedora/linux/releases/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class FedoraChecker(BaseChecker):
    RELEASES_URL = "https://dl.fedoraproject.org/pub/fedora/linux/releases/"

    def _fetch_release_numbers(self) -> list[int]:
        try:
            resp = requests.get(self.RELEASES_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(\d+)/?"', resp.text)
            return sorted(set(int(v) for v in versions), reverse=True)
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    # Spins dans le répertoire Spins/ (KDE a son propre répertoire depuis F41+)
    _SPINS = {"Xfce", "Cinnamon", "MATE", "i3", "LXQt", "Budgie", "Sway"}
    # MATE s'appelle MATE_Compiz dans les noms de fichiers
    _SPIN_FILENAME = {"MATE": "MATE_Compiz"}

    # Répertoire de base dl.fedoraproject.org
    _BASE = "https://dl.fedoraproject.org/pub/fedora/linux/releases/"

    def _fetch_iso_for_release(self, release: int) -> Optional[VersionInfo]:
        variant = self.variant or "Workstation"
        if variant == "Workstation":
            iso_dir = f"{self._BASE}{release}/Workstation/x86_64/iso/"
            # Nouveau format: Fedora-Workstation-Live-43-1.6.x86_64.iso
            # Ancien format: Fedora-Workstation-Live-x86_64-42-1.1.iso
            patterns = [
                r"(Fedora-Workstation-Live-(\d+)-[\d.]+\.x86_64\.iso)",
                r"(Fedora-Workstation-Live-x86_64-(\d+)-[\d.]+\.iso)",
            ]
            variant_label = "Workstation Live"
        elif variant == "KDE":
            # Depuis F41 : répertoire KDE/ dédié, nom inclut "Desktop"
            iso_dir = f"{self._BASE}{release}/KDE/x86_64/iso/"
            patterns = [
                r"(Fedora-KDE-Desktop-Live-(\d+)-[\d.]+\.x86_64\.iso)",
                r"(Fedora-KDE-Desktop-Live-x86_64-(\d+)-[\d.]+\.iso)",
            ]
            variant_label = "KDE"
        elif variant == "Silverblue":
            # Répertoire Silverblue/ dédié (plus dans Spins/)
            iso_dir = f"{self._BASE}{release}/Silverblue/x86_64/iso/"
            patterns = [
                r"(Fedora-Silverblue-ostree-x86_64-(\d+)-[\d.]+\.iso)",
                r"(Fedora-Silverblue-ostree-(\d+)-[\d.]+\.x86_64\.iso)",
            ]
            variant_label = "Silverblue"
        elif variant == "Kinoite":
            # Répertoire Kinoite/ dédié (plus dans Spins/)
            iso_dir = f"{self._BASE}{release}/Kinoite/x86_64/iso/"
            patterns = [
                r"(Fedora-Kinoite-ostree-x86_64-(\d+)-[\d.]+\.iso)",
                r"(Fedora-Kinoite-ostree-(\d+)-[\d.]+\.x86_64\.iso)",
            ]
            variant_label = "Kinoite"
        elif variant in self._SPINS:
            # Spins : Xfce, Cinnamon, MATE, i3, LXQt, Budgie, Sway
            iso_dir = f"{self._BASE}{release}/Spins/x86_64/iso/"
            fname = self._SPIN_FILENAME.get(variant, variant)
            patterns = [
                rf"(Fedora-{fname}-Live-(\d+)-[\d.]+\.x86_64\.iso)",
                rf"(Fedora-{fname}-Live-x86_64-(\d+)-[\d.]+\.iso)",
            ]
            variant_label = f"{variant} Spin"
        elif variant == "Server":
            iso_dir = (
                f"https://dl.fedoraproject.org/pub/fedora/linux/releases/"
                f"{release}/Server/x86_64/iso/"
            )
            patterns = [
                r"(Fedora-Server-dvd-x86_64-(\d+)-[\d.]+\.iso)",
                r"(Fedora-Server-dvd-(\d+)-[\d.]+\.x86_64\.iso)",
            ]
            variant_label = "Server DVD"
        else:
            iso_dir = (
                f"https://dl.fedoraproject.org/pub/fedora/linux/releases/"
                f"{release}/Server/x86_64/iso/"
            )
            patterns = [
                r"(Fedora-Server-dvd-x86_64-(\d+)-[\d.]+\.iso)",
                r"(Fedora-Server-dvd-(\d+)-[\d.]+\.x86_64\.iso)",
            ]
            variant_label = "Server DVD"

        try:
            resp = requests.get(iso_dir, timeout=10)
            resp.raise_for_status()
            for pattern in patterns:
                matches = re.findall(pattern, resp.text)
                if matches:
                    filename, ver = matches[0]
                    # Le nom du fichier CHECKSUM varie selon la variante
                    # (ex: "Fedora-Workstation-44-1.7-x86_64-CHECKSUM") : on le
                    # retrouve dans le même listing plutôt que de le deviner.
                    checksum = None
                    cm = re.search(r'href="([^"]*-CHECKSUM)"', resp.text)
                    if cm:
                        checksum = fetch_bsd_sha256(iso_dir + cm.group(1), filename)
                    return VersionInfo(
                        version=ver,
                        download_url=iso_dir + filename,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha256",
                        release_notes_url=f"https://fedoraproject.org/wiki/Releases/{release}/ChangeSet",
                        variant_label=f"{variant_label} F{release}",
                    )
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            pass
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        releases = self._fetch_release_numbers()
        for r in releases:
            info = self._fetch_iso_for_release(r)
            if info:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        releases = self._fetch_release_numbers()
        results = []
        for r in releases:
            info = self._fetch_iso_for_release(r)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        # Nouveau format : Fedora-KDE-Desktop-Live-43-1.6.x86_64.iso
        #                  Fedora-Workstation-Live-43-1.6.x86_64.iso
        m = re.search(
            r"Fedora-[\w-]+-(?:Live|ostree|dvd|netinst)-(\d+)-[\d.]+\.x86_64\.iso",
            filename, re.IGNORECASE
        )
        if m:
            return m.group(1)
        # Format ostree : Fedora-Silverblue-ostree-x86_64-42-1.1.iso
        m = re.search(
            r"Fedora-[\w-]+-(?:ostree|dvd|netinst)-x86_64-(\d+)-[\d.]+\.iso",
            filename, re.IGNORECASE
        )
        if m:
            return m.group(1)
        # Ancien format Live : Fedora-KDE-Live-x86_64-42-1.1.iso
        m = re.search(
            r"Fedora-[\w-]+-Live-x86_64-(\d+)-[\d.]+\.iso",
            filename, re.IGNORECASE
        )
        return m.group(1) if m else None
