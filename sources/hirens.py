"""
Hiren's BootCD PE — outil de diagnostic/récupération Windows PE.
Source : https://www.hirensbootcd.org/download/
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


class HirensChecker(BaseChecker):
    DL_PAGE = "https://www.hirensbootcd.org/download/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.DL_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            text = resp.text

            # Cherche les liens ISO : Hirens.BootCD.1.0.2.iso ou HBCD_PE_x64.iso
            links = re.findall(
                r'href="([^"]+(?:Hirens\.BootCD\.[^"]+\.iso|HBCD_PE_x64\.iso))"',
                text, re.IGNORECASE
            )
            results = []
            seen = set()
            for url in links:
                if url in seen:
                    continue
                seen.add(url)
                filename = url.split("/")[-1].split("?")[0]
                if not url.startswith("http"):
                    url = "https://www.hirensbootcd.org" + url
                m = re.search(r"Hirens\.BootCD\.([\d.]+)\.iso", filename, re.IGNORECASE)
                version = m.group(1) if m else "latest"
                # L'empreinte SHA-256 de l'ISO est écrite en dur dans le
                # tableau de la page (pas de fichier .sha256 séparé).
                sum_m = re.search(
                    r"ISO SHA-256</strong></td>\s*<td[^>]*>([0-9a-fA-F]{64})",
                    text, re.IGNORECASE
                )
                checksum = sum_m.group(1).lower() if sum_m else None
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label="PE x64",
                    release_notes_url="https://www.hirensbootcd.org/",
                ))

            # Cherche aussi la version dans le texte si pas de lien direct
            if not results:
                m = re.search(r"Hirens\.BootCD\.([\d.]+)", text, re.IGNORECASE)
                if m:
                    version = m.group(1)
                    filename = f"Hirens.BootCD.{version}.iso"
                    results.append(VersionInfo(
                        version=version,
                        download_url=f"https://www.hirensbootcd.org/files/{filename}",
                        filename=filename,
                        variant_label="PE x64",
                    ))
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Hirens\.BootCD\.([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None
