"""Tests unitaires pour sources/base.py (BaseChecker / VersionInfo)"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sources.base import BaseChecker, VersionInfo


class DummyChecker(BaseChecker):
    def __init__(self, version="1.0.0", variant=None):
        super().__init__(variant=variant)
        self._version = version

    def get_latest_version(self):
        return VersionInfo(version=self._version, download_url="http://example.com/test.iso",
                           filename="test.iso")

    def parse_local_version(self, filename):
        import re
        m = re.search(r"-([\d.]+)\.iso", filename)
        return m.group(1) if m else None


class TestVersionInfo:
    def test_defaults(self):
        v = VersionInfo(version="1.0", download_url="http://x.com/f.iso", filename="f.iso")
        assert v.stable is True
        assert v.checksum is None
        assert v.checksum_type is None
        assert v.arch == "amd64"

    def test_full_fields(self):
        v = VersionInfo(
            version="2.0",
            download_url="http://x.com/f.iso",
            filename="f.iso",
            checksum="abc123",
            checksum_type="sha256",
            stable=False,
            variant_label="Server",
        )
        assert v.checksum == "abc123"
        assert v.stable is False
        assert v.variant_label == "Server"


class TestBaseChecker:
    def test_is_outdated_simple(self):
        checker = DummyChecker()
        assert checker.is_outdated("1.0.0", "2.0.0") is True
        assert checker.is_outdated("2.0.0", "1.0.0") is False
        assert checker.is_outdated("1.0.0", "1.0.0") is False

    def test_is_outdated_complex_versions(self):
        checker = DummyChecker()
        assert checker.is_outdated("22.04", "24.04") is True
        assert checker.is_outdated("24.04", "22.04") is False

    def test_is_outdated_invalid_version_fallback(self):
        checker = DummyChecker()
        # Lexicographic fallback
        assert checker.is_outdated("2023.01", "2024.01") is True

    def test_get_all_versions_default(self):
        checker = DummyChecker("3.0.0")
        versions = checker.get_all_versions()
        assert len(versions) == 1
        assert versions[0].version == "3.0.0"

    def test_parse_local_version(self):
        checker = DummyChecker()
        assert checker.parse_local_version("ubuntu-22.04.iso") == "22.04"
        assert checker.parse_local_version("noversion.iso") is None

    def test_variant_passed(self):
        checker = DummyChecker(variant="KDE")
        assert checker.variant == "KDE"
