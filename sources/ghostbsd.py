"""
Vérificateur de version pour GhostBSD.
Source : https://www.ghostbsd.org/download — la page officielle liste trois
éditions (MATE par défaut, XFCE, GERSHWIN) avec un lien direct et son
empreinte SHA256 écrite en clair juste en dessous (pas de fichier séparé
à télécharger pour l'obtenir, même si un sidecar .sha256 existe aussi).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_VARIANTS = {
    "mate":     None,        # image par défaut, pas de suffixe dans le nom
    "xfce":     "XFCE",
    "gershwin": "GERSHWIN",
}


class GhostBSDChecker(BaseChecker):
    DOWNLOAD_PAGE = "https://www.ghostbsd.org/download"
    # Repli si la page officielle est injoignable (pas d'empreinte alors)
    RELEASES_URL = "https://download.ghostbsd.org/releases/amd64/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = (self.variant or "mate").lower()
        suffix = _VARIANTS.get(variant)

        try:
            resp = requests.get(
                self.DOWNLOAD_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            # Chaque édition : lien direct vers l'ISO puis, plus loin dans le
            # même bloc, "SHA256 Checksum: <empreinte>".
            pattern = re.compile(
                r'href="(https://download\.ghostbsd\.org/releases/amd64/[^"]+/'
                r'GhostBSD-[^"/]+\.iso)".*?SHA256 Checksum:</b>\s*<a[^>]*>([0-9a-fA-F]{64})</a>',
                re.DOTALL
            )
            for url, checksum in pattern.findall(resp.text):
                filename = url.split("/")[-1]
                # Sans suffixe = édition par défaut (MATE) : exclut XFCE/GERSHWIN
                if not suffix and ("-XFCE" in filename.upper() or "-GERSHWIN" in filename.upper()):
                    continue
                if suffix and not filename.upper().endswith(f"-{suffix}.ISO"):
                    continue
                m = re.search(r"GhostBSD-([\d.]+-R[\d.]+(?:p\d+)?)", filename)
                version = m.group(1) if m else "latest"
                return [VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum.lower(),
                    checksum_type="sha256",
                    variant_label=variant.upper() if suffix else "MATE",
                )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)

        # Repli : listing du miroir (pas d'empreinte disponible ici)
        try:
            resp = requests.get(self.RELEASES_URL, timeout=10)
            resp.raise_for_status()
            versions_dirs = re.findall(r'href="(\d+(?:\.\d+)*(?:-[A-Za-z0-9.]+)?)/?"', resp.text)
            from packaging.version import Version as PV, InvalidVersion
            def sort_key(v):
                try:
                    return PV(v.split("-")[0])
                except InvalidVersion:
                    return PV("0")
            unique = sorted(set(versions_dirs), key=sort_key, reverse=True)
            for ver_dir in unique[:5]:
                dir_url = f"{self.RELEASES_URL}{ver_dir}/"
                try:
                    r2 = requests.get(dir_url, timeout=8)
                    r2.raise_for_status()
                    if suffix:
                        isos = re.findall(rf"(GhostBSD-[\d.-]+p?\d*-{suffix}\.iso)", r2.text, re.IGNORECASE)
                    else:
                        isos = [f for f in re.findall(r"(GhostBSD-[\d.-]+p?\d*\.iso)", r2.text)
                                if "-XFCE" not in f.upper() and "-GERSHWIN" not in f.upper()]
                    for filename in isos[:1]:
                        return [VersionInfo(
                            version=ver_dir,
                            download_url=dir_url + filename,
                            filename=filename,
                            variant_label=variant.upper() if suffix else "MATE",
                        )]
                except Exception as _exc:
                    logger.debug("%s: échec ignoré : %s", __name__, _exc)
                    continue
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)

        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"GhostBSD-([\d.]+-R[\d.]+(?:p\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None
