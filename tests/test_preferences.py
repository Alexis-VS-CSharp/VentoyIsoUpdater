"""Tests unitaires pour core/preferences.py"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def isolated_prefs(tmp_path):
    """Patches the prefs paths to point to an isolated temp folder."""
    prefs_dir  = tmp_path / "config"
    prefs_file = prefs_dir / "prefs.json"
    with patch("core.preferences._PREFS_DIR",  prefs_dir), \
         patch("core.preferences._PREFS_FILE", prefs_file):
        import core.preferences as prefs
        yield prefs


class TestPreferences:
    def test_load_defaults_when_missing(self, isolated_prefs):
        p = isolated_prefs
        result = p.load()
        assert isinstance(result, dict)
        assert "download_folder" in result
        assert "stable_only" in result

    def test_save_and_reload(self, isolated_prefs):
        p = isolated_prefs
        data = p.load()
        data["stable_only"] = False
        data["last_drive"] = "/media/user/KEY"
        p.save(data)
        reloaded = p.load()
        assert reloaded["stable_only"] is False
        assert reloaded["last_drive"] == "/media/user/KEY"

    def test_get_key(self, isolated_prefs):
        p = isolated_prefs
        data = p.load()
        data["stable_only"] = True
        p.save(data)
        assert p.get("stable_only") is True

    def test_set_key(self, isolated_prefs):
        p = isolated_prefs
        p.set_key("stable_only", False)
        assert p.get("stable_only") is False

    def test_unknown_key_ignored(self, isolated_prefs):
        p = isolated_prefs
        p.set_key("unknown_key_xyz", 42)
        data = p.load()
        assert "unknown_key_xyz" not in data

    def test_corrupt_json_returns_defaults(self, isolated_prefs, tmp_path):
        p = isolated_prefs
        prefs_file = tmp_path / "config" / "prefs.json"
        prefs_file.parent.mkdir(parents=True, exist_ok=True)
        prefs_file.write_text("{ corrupt json !!")
        result = p.load()
        assert isinstance(result, dict)
        assert "stable_only" in result
