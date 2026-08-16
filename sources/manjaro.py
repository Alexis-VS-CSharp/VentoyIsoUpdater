"""
Manjaro Linux.
Source : https://manjaro.org/products/download/x86/_payload.json
Les URLs directes sont exposées dans le payload Nuxt.js de la page de téléchargement.
"""
import re
import json
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

# Correspondance variant → clé dans le payload JSON
_VARIANT_KEY = {
    "kde":   "plasma",
    "gnome": "gnome",
    "xfce":  "xfce",
}

_PAYLOAD_URL = "https://manjaro.org/products/download/x86/_payload.json"


class ManjaroChecker(BaseChecker):

    def _fetch_data(self) -> dict:
        try:
            # Récupère d'abord la page pour obtenir l'UID du payload
            page = requests.get(
                "https://manjaro.org/products/download/x86",
                timeout=10, headers={"User-Agent": "Mozilla/5.0"}
            )
            page.raise_for_status()
            m = re.search(r'_payload\.json\?([a-z0-9-]+)', page.text)
            url = f"{_PAYLOAD_URL}?{m.group(1)}" if m else _PAYLOAD_URL
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            # Le payload est une liste JSON dont le 3e élément contient une chaîne JSON imbriquée
            outer = resp.json()
            raw = next((x for x in outer if isinstance(x, str) and '"official"' in x), None)
            if raw:
                return json.loads(raw)
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            pass
        return {}

    def _make_entries(self, data: dict, variant_key: str) -> list[VersionInfo]:
        results = []
        official = data.get("official", {})
        entry = official.get(variant_key, {})
        if not entry:
            return results

        for label, iso_entry in [("Full", entry), ("Minimal", entry.get("minimal", {}))]:
            url = iso_entry.get("image", "")
            if not url or not url.endswith(".iso"):
                continue
            filename = url.split("/")[-1]
            m = re.search(r"manjaro-[^-]+-(\d+\.\d+(?:\.\d+)?)", filename, re.IGNORECASE)
            version = m.group(1) if m else "latest"
            # Le payload donne directement l'URL du sidecar .sha256
            checksum_url = iso_entry.get("checksum", "")
            checksum = fetch_sha256sums(checksum_url, filename) if checksum_url else None
            results.append(VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                release_notes_url="https://manjaro.org/news/",
                variant_label=label,
            ))
        return results

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "kde"
        key = _VARIANT_KEY.get(variant, variant)
        data = self._fetch_data()
        return self._make_entries(data, key)

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"manjaro-[^-]+-(\d+\.\d+(?:\.\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None
