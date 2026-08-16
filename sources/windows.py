"""
Vérificateur pour les ISO Windows.
Microsoft ne fournit pas d'API publique pour la vérification automatique.
→ Ce checker détecte l'ISO et signale qu'une vérification manuelle est requise.
"""

import re
from typing import Optional
from sources.base import BaseChecker, VersionInfo


class WindowsChecker(BaseChecker):
    HOMEPAGES = {
        "10": "https://www.microsoft.com/software-download/windows10ISO",
        "11": "https://www.microsoft.com/software-download/windows11",
        "server2022": "https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2022",
        "server2019": "https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019",
    }

    def get_latest_version(self) -> Optional[VersionInfo]:
        # Pas de vérification automatique possible pour Microsoft
        # On retourne None pour indiquer "vérification manuelle"
        return None

    def parse_local_version(self, filename: str) -> Optional[str]:
        # Essaie d'extraire un numéro de build ou d'édition du nom de fichier
        # Ex: Win10_22H2_French_x64.iso → 22H2
        m = re.search(r"(\d{2}H\d)", filename, re.IGNORECASE)
        if m:
            return m.group(1)
        # Serveur : SERVER_EVAL_x64FRE_en-us_DV9.iso → pas de version claire
        return None

    def get_homepage(self) -> str:
        return self.HOMEPAGES.get(self.variant or "11", "https://microsoft.com")
