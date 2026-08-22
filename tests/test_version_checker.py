"""Tests unitaires pour core/version_checker.py"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.version_checker import (
    UpdateStatus,
    CheckResult,
    _check_one,
    check_all,
    _CHECKER_REGISTRY,
    _load_checkers,
)
from core.ventoy_scanner import IsoEntry
from sources.base import VersionInfo


def make_iso(distro_id=None, local_version=None, filename="test.iso"):
    return IsoEntry(
        filename=filename, path="/mnt/usb/test.iso",
        folder="linux", size_bytes=1024,
        distro_id=distro_id, local_version=local_version
    )


SAMPLE_DB = {
    "distros": [
        {
            "id": "ubuntu",
            "name": "Ubuntu",
            "checker": "ubuntu",
            "checker_variant": None,
            "filename_patterns": [r"ubuntu"],
            "grub_class": "ubuntu",
        },
        {
            "id": "windows11",
            "name": "Windows 11",
            "checker": "windows",
            "filename_patterns": [r"Win11"],
            "grub_class": "windows",
        },
    ]
}


class TestCheckOne:
    def test_unknown_distro(self):
        iso = make_iso(distro_id=None)
        result = _check_one(iso, SAMPLE_DB)
        assert result.status == UpdateStatus.UNKNOWN

    def test_windows_returns_manual(self):
        iso = make_iso(distro_id="windows11")
        result = _check_one(iso, SAMPLE_DB)
        assert result.status == UpdateStatus.MANUAL

    def test_checker_not_found(self):
        db = {"distros": [{"id": "myos", "checker": "nonexistent_checker",
                            "name": "MyOS", "filename_patterns": []}]}
        iso = make_iso(distro_id="myos")
        result = _check_one(iso, db)
        assert result.status == UpdateStatus.UNKNOWN

    def test_returns_error_on_network_exception(self):
        """The exception must be raised by get_latest_version(), not by instantiation."""
        _load_checkers()
        db = {"distros": [{"id": "ubuntu", "checker": "ubuntu", "name": "Ubuntu",
                            "filename_patterns": [], "checker_variant": None}]}
        iso = make_iso(distro_id="ubuntu", local_version="22.04")
        mock_instance = MagicMock()
        mock_instance.get_latest_version.side_effect = Exception("network error")
        mock_cls = MagicMock(return_value=mock_instance)
        with patch.dict(_CHECKER_REGISTRY, {"ubuntu": mock_cls}):
            result = _check_one(iso, db)
        assert result.status == UpdateStatus.ERROR

    def test_unknown_local_version(self):
        _load_checkers()
        db = {"distros": [{"id": "ubuntu", "checker": "ubuntu", "name": "Ubuntu",
                            "filename_patterns": [], "checker_variant": None}]}
        iso = make_iso(distro_id="ubuntu", local_version=None, filename="ubuntu-badname.iso")
        mock_checker = MagicMock()
        mock_checker.return_value.get_latest_version.return_value = VersionInfo(
            version="24.04", download_url="http://x.com/u.iso", filename="u.iso"
        )
        mock_checker.return_value.parse_local_version.return_value = None
        with patch.dict(_CHECKER_REGISTRY, {"ubuntu": mock_checker}):
            result = _check_one(iso, db)
        assert result.status == UpdateStatus.UNKNOWN


class TestCheckAll:
    def test_calls_on_result(self):
        isos = [make_iso(distro_id=None), make_iso(distro_id=None)]
        results_collected = []
        check_all(isos, {}, on_result=results_collected.append, max_workers=2)
        assert len(results_collected) == 2

    def test_returns_all_results(self):
        isos = [make_iso(distro_id=None) for _ in range(4)]
        results = check_all(isos, {}, max_workers=2)
        assert len(results) == 4

    def test_handles_empty_list(self):
        results = check_all([], {})
        assert results == []


class TestUpdateStatus:
    def test_enum_values(self):
        assert UpdateStatus.UP_TO_DATE.value == "À jour"
        assert UpdateStatus.OUTDATED.value == "Mise à jour disponible"
        assert UpdateStatus.UNKNOWN.value == "Non reconnue"
        assert UpdateStatus.ERROR.value == "Erreur"
