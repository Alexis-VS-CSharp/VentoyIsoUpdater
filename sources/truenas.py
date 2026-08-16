"""TrueNAS SCALE.
Source : https://www.truenas.com/download/
Les liens ISO sont embarqués directement dans le HTML de la page de téléchargement.
URL réelles : https://download.sys.truenas.net/TrueNAS-SCALE-{CodeName}/{ver}/TrueNAS-SCALE-{ver}.iso
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_DL_PAGE = "https://www.truenas.com/download/"
# Pattern extrait depuis le HTML : les liens ISO sont en dur dans la page
_ISO_RE = re.compile(
    r'https://download\.sys\.truenas\.net/'
    r'(TrueNAS-SCALE-(\w+))/'       # groupe 1 = dossier codename, groupe 2 = codename seul
    r'([\d.]+)/'                     # groupe 3 = version
    r'(TrueNAS-SCALE-[\d.]+\.iso)',  # groupe 4 = nom de fichier
    re.IGNORECASE,
)


class TrueNASChecker(BaseChecker):

    def _fetch_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(_DL_PAGE, timeout=15)
            resp.raise_for_status()
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

        seen: set[str] = set()
        results: list[VersionInfo] = []

        for m in _ISO_RE.finditer(resp.text):
            codename_dir = m.group(1)   # ex: TrueNAS-SCALE-Fangtooth
            codename     = m.group(2)   # ex: Fangtooth
            version      = m.group(3)   # ex: 25.04.2.6
            filename     = m.group(4)   # ex: TrueNAS-SCALE-25.04.2.6.iso
            url          = m.group(0)

            if filename in seen:
                continue
            seen.add(filename)

            # Stable si mois == 04 (convention TrueNAS : .04 = production, .10 = beta)
            parts = version.split(".")
            month = parts[1] if len(parts) >= 2 else "0"
            stable = (month == "04")

            # Essaie de récupérer le sha256
            sha_url = url + ".sha256"
            checksum = None
            try:
                r2 = requests.get(sha_url, timeout=8)
                if r2.ok:
                    # Ligne du type "abc123...  TrueNAS-SCALE-25.04.2.6.iso"
                    checksum = r2.text.split()[0] if r2.text.strip() else None
            except Exception as _exc:
                logger.debug("%s: échec ignoré : %s", __name__, _exc)
                pass

            results.append(VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256" if checksum else None,
                release_notes_url="https://www.truenas.com/docs/",
                variant_label=f"SCALE {codename}",
                stable=stable,
            ))

        # Trie par version décroissante
        try:
            from packaging.version import Version as PV, InvalidVersion
            results.sort(key=lambda v: _pv(v.version), reverse=True)
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            pass

        return results

    def get_latest_version(self) -> Optional[VersionInfo]:
        all_v = self._fetch_versions()
        # Préfère la dernière version stable
        stable = [v for v in all_v if v.stable]
        return (stable or all_v or [None])[0]

    def get_all_versions(self) -> list[VersionInfo]:
        return self._fetch_versions()

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"TrueNAS-(?:CORE|SCALE)[_-]([\d.]+(?:U[\d.]+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None


def _pv(v: str):
    from packaging.version import Version as PV, InvalidVersion
    try:
        return PV(v)
    except InvalidVersion:
        return PV("0")
