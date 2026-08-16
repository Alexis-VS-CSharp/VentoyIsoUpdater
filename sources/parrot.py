"""
Vérificateur de version pour Parrot OS.
Source : https://download.parrot.sh/parrot/iso/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class ParrotChecker(BaseChecker):
    BASE_URL = "https://download.parrot.sh/parrot/iso/"

    def _fetch_versions(self) -> list[str]:
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            # \d+ en tête : exclut le lien "dossier parent" (href="../") que
            # [\d.]+ capturerait aussi ('..' est fait uniquement de points).
            versions = re.findall(r'href="(\d+(?:\.\d+)*)/?"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(versions))
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        edition = self.variant or "home"
        dir_url = f"{self.BASE_URL}{version}/"

        # Essai 1 : liste le répertoire pour trouver le bon nom de fichier
        try:
            resp = requests.get(dir_url, timeout=10)
            resp.raise_for_status()
            # Cherche les ISOs pour cette édition
            isos = re.findall(
                rf"(Parrot-{re.escape(edition)}-[\d.]+[^\"'\s<>]*\.iso)",
                resp.text, re.IGNORECASE
            )
            if not isos:
                # Tente n'importe quel ISO contenant l'édition
                isos = re.findall(
                    rf"(Parrot-{re.escape(edition)}[^\"'\s<>]*_amd64\.iso)",
                    resp.text, re.IGNORECASE
                )
            for filename in isos[:1]:
                url = dir_url + filename
                # Fichier signé PGP en clair, contient md5/sha256/sha512
                # pour chaque image ; la longueur de l'empreinte suffit à
                # cibler la bonne section.
                checksum = fetch_sha256sums(dir_url + "signed-hashes.txt", filename)
                return VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label=edition.capitalize(),
                )
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            pass

        # Essai 2 : HEAD direct avec plusieurs patterns de noms
        candidates = [
            f"Parrot-{edition}-{version}_amd64.iso",
            f"Parrot-{edition}-{version}-amd64.iso",
            f"Parrot-{edition}_{version}_amd64.iso",
        ]
        for filename in candidates:
            url = dir_url + filename
            try:
                r = requests.head(url, timeout=8, allow_redirects=True)
                if r.status_code in (200, 302):
                    checksum = fetch_sha256sums(dir_url + "signed-hashes.txt", filename)
                    return VersionInfo(
                        version=version,
                        download_url=url,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha256",
                        variant_label=edition.capitalize(),
                    )
            except Exception as _exc:
                logger.debug("%s: échec ignoré : %s", __name__, _exc)
                continue
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        for v in self._fetch_versions():
            info = self._make_version_info(v)
            if info:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        for v in self._fetch_versions():
            info = self._make_version_info(v)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Parrot-(?:home|security)-([\d.]+)[_-]", filename, re.IGNORECASE)
        return m.group(1) if m else None
