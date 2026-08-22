"""
Checker for Windows ISOs.
Microsoft doesn't provide a public API for automatic verification.
-> This checker detects the ISO and signals that manual verification is required.
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
        # No automatic verification possible for Microsoft
        # Returns None to indicate "manual verification"
        return None

    def parse_local_version(self, filename: str) -> Optional[str]:
        # Tries to extract a build/edition number from the filename
        # E.g.: Win10_22H2_French_x64.iso -> 22H2
        m = re.search(r"(\d{2}H\d)", filename, re.IGNORECASE)
        if m:
            return m.group(1)
        # Server: SERVER_EVAL_x64FRE_en-us_DV9.iso -> no clear version
        return None

    def get_homepage(self) -> str:
        return self.HOMEPAGES.get(self.variant or "11", "https://microsoft.com")
