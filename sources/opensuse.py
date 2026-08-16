"""
openSUSE Leap et Tumbleweed. Source : download.opensuse.org (voir
https://en.opensuse.org/SDB:Download_help#Checksums).

Le miroir mirrors.edge.kernel.org utilisé auparavant liste bien les fichiers
"Current.iso" dans son index, mais ce sont des liens morts (404) sur ce
miroir précis — aussi bien l'ISO que son ".sha256". download.opensuse.org
est le point d'entrée officiel : il redirige (302) vers un miroir qui sert
réellement le fichier, pour l'ISO comme pour l'empreinte.

Le fichier <iso>.sha256 récupéré après redirection référence le nom réel du
build (ex: "...-Build710.3-Media.iso"), pas "Current.iso" — on en extrait
donc l'unique empreinte SHA256 qu'il contient plutôt que de chercher une
correspondance exacte de nom de fichier.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


def _fetch_current_sha256(sha256_url: str) -> Optional[str]:
    """
    Récupère l'empreinte SHA256 d'un sidecar '<iso>.sha256' pointant sur
    "Current" : le fichier ne contient qu'une seule empreinte pertinente,
    sous son nom de build réel (ex: '...-Build710.3-Media.iso'), donc on
    prend la première trouvée plutôt que de matcher un nom de fichier exact.
    """
    try:
        resp = requests.get(sha256_url, timeout=10)
        resp.raise_for_status()
    except Exception as _exc:
        logger.debug("%s: échec ignoré : %s", __name__, _exc)
        return None
    m = re.search(r"^([0-9a-fA-F]{64})\s+\*?\S+\.iso\s*$", resp.text, re.MULTILINE)
    return m.group(1).lower() if m else None


class OpenSUSEChecker(BaseChecker):
    # variant: 'leap' ou 'tumbleweed'
    LEAP_URL = "https://download.opensuse.org/distribution/leap/"
    TW_URL   = "https://download.opensuse.org/tumbleweed/iso/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "leap"
        if variant == "tumbleweed":
            return self._fetch_tumbleweed()
        return self._fetch_leap()

    def _fetch_leap(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.LEAP_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(?:\./)?(\d+\.\d+)/"', resp.text)
            from packaging.version import Version as PV
            # Exclut la branche 42.x (ancienne, < 2018) — openSUSE est passé à 15.x
            unique = [v for v in dict.fromkeys(versions) if not v.startswith("42.")]
            unique.sort(key=lambda v: PV(v), reverse=True)

            results = []
            for ver in unique[:6]:
                iso_url = f"{self.LEAP_URL}{ver}/iso/"
                try:
                    r2 = requests.get(iso_url, timeout=8)
                    r2.raise_for_status()
                    isos = re.findall(
                        rf'(openSUSE-Leap-{re.escape(ver)}-DVD-x86_64-[^"]+\.iso)',
                        r2.text
                    )
                    if not isos:
                        isos = re.findall(r'(openSUSE-Leap-[\d.]+-[^"]+\.iso)', r2.text)
                    for filename in isos[:1]:
                        checksum = _fetch_current_sha256(iso_url + filename + ".sha256")
                        results.append(VersionInfo(
                            version=ver,
                            download_url=iso_url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url=f"https://doc.opensuse.org/release-notes/x86_64/openSUSE/Leap/{ver}/",
                            variant_label=f"Leap {ver}",
                            stable=True,
                        ))
                except Exception as _exc:
                    logger.debug("%s: échec ignoré : %s", __name__, _exc)
                    continue
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def _fetch_tumbleweed(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.TW_URL, timeout=10)
            resp.raise_for_status()
            isos = re.findall(
                r'(openSUSE-Tumbleweed-DVD-x86_64-[^"]+\.iso)',
                resp.text
            )
            results = []
            for filename in isos[:3]:
                m = re.search(r'Tumbleweed-DVD-x86_64-(\d+)', filename)
                version = m.group(1) if m else "latest"
                checksum = _fetch_current_sha256(self.TW_URL + filename + ".sha256")
                results.append(VersionInfo(
                    version=version,
                    download_url=self.TW_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://opensuse.github.io/openSUSE-release-tools/tumbleweed-review.html",
                    variant_label="Tumbleweed (Rolling)",
                    stable=False,
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"openSUSE-(?:Leap|Tumbleweed)[^-]*-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None
