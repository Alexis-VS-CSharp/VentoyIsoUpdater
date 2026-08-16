"""
Garuda Linux — performance Arch-based.
Source : https://iso.builds.garudalinux.org/iso/garuda/{edition}/{date}/

10 éditions officielles : cinnamon, dr460nized, dr460nized-gaming, gnome,
hyprland, i3, kde-lite, mokka, sway, xfce. Chaque ISO a un sidecar .sha256.

Le raccourci ".../latest/garuda/{edition}/latest.iso" existe mais pointe par
moments vers un build plus ancien que le dernier dossier daté réellement
présent (constaté : latest.iso -> build de mars alors qu'un build d'août est
disponible) — on liste donc toujours les dossiers datés et on prend le plus
récent, plutôt que de faire confiance à ce raccourci.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_EDITIONS = {
    "cinnamon", "dr460nized", "dr460nized-gaming", "gnome", "hyprland",
    "i3", "kde-lite", "mokka", "sway", "xfce",
}


class GarudaChecker(BaseChecker):
    INDEX_URL = "https://iso.builds.garudalinux.org/iso/garuda/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant if self.variant in _EDITIONS else "dr460nized"
        dir_url = f"{self.INDEX_URL}{variant}/"
        try:
            resp = requests.get(dir_url, timeout=10)
            resp.raise_for_status()
            date_dirs = sorted(set(re.findall(r'href="(\d{6})/?"', resp.text)), reverse=True)

            for date_dir in date_dirs[:5]:
                iso_dir_url = f"{dir_url}{date_dir}/"
                try:
                    r2 = requests.get(iso_dir_url, timeout=8)
                    r2.raise_for_status()
                    m = re.search(r'href="(garuda-[^"]+\.iso)"', r2.text)
                    if not m:
                        continue
                    filename = m.group(1)
                    checksum = fetch_sha256sums(iso_dir_url + filename + ".sha256", filename)
                    return [VersionInfo(
                        version=date_dir,
                        download_url=iso_dir_url + filename,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha256",
                        release_notes_url="https://garudalinux.org/news",
                        variant_label=variant,
                    )]
                except Exception as _exc:
                    logger.debug("%s: échec ignoré : %s", __name__, _exc)
                    continue
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)

        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"garuda[^-]*-[^-]+-[^-]+-(\d{6})", filename, re.IGNORECASE)
        return m.group(1) if m else None
