"""
MX Linux. Source : miroir AARNet (HTTPS, structure identique à SourceForge
mais sans ses blocages anti-bot occasionnels — liste complète des miroirs :
https://rsync-mxlinux.org/mirmon/index.html).
Empreintes : sidecar "<iso>.sha256" à côté de chaque image, voir
https://mxlinux.org/wiki/system/iso-download-mirrors/#checksumsignatures
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

# Mapping variant -> sous-dossier et fragment de nom d'ISO
_VARIANT_MAP = {
    "xfce":    {"folder": "Xfce",    "tag": "_Xfce_"},
    "kde":     {"folder": "KDE",     "tag": "_KDE_"},
    "fluxbox": {"folder": "Fluxbox", "tag": "_Fluxbox_"},
}

_MIRROR_BASE = "https://mirror.aarnet.edu.au/pub/mxlinux/iso/MX/Final"


class MXLinuxChecker(BaseChecker):
    """Supports variant='xfce' (default), 'kde', 'fluxbox'."""

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = (self.variant or "xfce").lower()
        info = _VARIANT_MAP.get(variant, _VARIANT_MAP["xfce"])
        folder, tag = info["folder"], info["tag"]
        dir_url = f"{_MIRROR_BASE}/{folder}/"

        try:
            resp = requests.get(dir_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

            # Match ISO filenames like MX-25.2_Xfce_x64.iso (standard) et
            # MX-25.2_Xfce_ahs_x64.iso (variante "advanced hardware support")
            pattern = re.compile(
                r'href="(MX-([\d.]+)' + re.escape(tag) + r'(ahs_)?x64\.iso)"',
                re.IGNORECASE,
            )
            matches = pattern.findall(resp.text)

            results = []
            for filename, version, is_ahs in matches:
                checksum = fetch_sha256sums(dir_url + filename + ".sha256", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=dir_url + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://mxlinux.org/blog/",
                    variant_label=f"{folder}{' AHS' if is_ahs else ''}",
                ))

            # Trie : version la plus récente d'abord, non-ahs avant ahs
            from packaging.version import Version as PV, InvalidVersion

            def sort_key(x: VersionInfo):
                try:
                    pv = PV(x.version)
                except InvalidVersion:
                    pv = PV("0")
                ahs_penalty = 1 if "AHS" in (x.variant_label or "") else 0
                return (pv, -ahs_penalty)

            results.sort(key=sort_key, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"MX-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None
