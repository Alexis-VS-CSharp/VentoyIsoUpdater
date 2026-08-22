"""Tests unitaires pour core/downloader.py"""

import os
import sys
import pytest
import tempfile
import shutil
import threading
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.downloader import download_logo, DownloadError


@pytest.fixture
def tmp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestDownloadLogo:
    def test_local_prefix_missing_file(self, tmp_dir):
        dest = os.path.join(tmp_dir, "logo.png")
        ok, err = download_logo("local:nonexistent.png", dest)
        assert ok is False
        assert err is not None

    def test_local_prefix_existing_file(self, tmp_dir):
        # Create a valid PNG file in assets/logos
        import os
        assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "logos"
        )
        if not os.path.isdir(assets_dir):
            pytest.skip("assets/logos/ not found")
        logos = [f for f in os.listdir(assets_dir) if f.endswith(".png")]
        if not logos:
            pytest.skip("No PNG in assets/logos/")
        dest = os.path.join(tmp_dir, "test_logo.png")
        ok, err = download_logo(f"local:{logos[0]}", dest)
        assert ok is True, f"Expected success, got error: {err}"
        assert os.path.isfile(dest)

    def test_http_connection_error(self, tmp_dir):
        dest = os.path.join(tmp_dir, "logo.png")
        with patch("requests.get", side_effect=Exception("Connection refused")):
            ok, err = download_logo("http://localhost:1/nonexistent.png", dest)
        assert ok is False
        assert err is not None

    def test_http_timeout(self, tmp_dir):
        import requests
        dest = os.path.join(tmp_dir, "logo.png")
        with patch("requests.get", side_effect=requests.Timeout()):
            ok, err = download_logo("http://localhost:1/test.png", dest)
        assert ok is False
        assert "délai" in (err or "").lower() or err is not None


    def test_http_size_limit(self, tmp_dir):
        """An oversized HTTP logo is rejected without exhausting RAM."""
        dest = os.path.join(tmp_dir, "logo.png")
        # Simulates content > 5 MB returned chunk by chunk
        big_chunk = b"x" * (6 * 1024 * 1024)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_resp.iter_content = MagicMock(return_value=iter([big_chunk]))
        with patch("requests.get", return_value=mock_resp):
            ok, err = download_logo("http://example.com/huge.png", dest)
        assert ok is False
        assert err is not None and "5 MB" in err

    def test_atomic_replace_overwrites_dest(self, tmp_dir):
        """os.replace() overwrites the existing destination file."""
        from core.downloader import download_file
        import hashlib
        dest = os.path.join(tmp_dir, "out.iso")
        # Creates an existing destination file
        with open(dest, "wb") as f:
            f.write(b"old content")
        content = b"new content"
        sha = hashlib.sha256(content).hexdigest()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"content-length": str(len(content))}
        mock_resp.iter_content = MagicMock(return_value=iter([content]))
        with patch("requests.get", return_value=mock_resp):
            result = download_file("http://example.com/out.iso", dest,
                                   checksum=sha, checksum_type="sha256")
        assert result == dest
        with open(dest, "rb") as f:
            assert f.read() == content


class TestDownloadFile:
    def test_cancel_event_stops_download(self, tmp_dir):
        from core.downloader import download_file
        cancel = threading.Event()
        cancel.set()  # Already cancelled

        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.iter_content = MagicMock(return_value=iter([b"x" * 100]))

        dest = os.path.join(tmp_dir, "test.iso")
        with patch("requests.get", return_value=mock_response):
            with pytest.raises(DownloadError, match="annulé"):
                download_file("http://example.com/test.iso", dest, cancel_event=cancel)

    def test_part_file_cleaned_on_error(self, tmp_dir):
        """The .part file is removed if the download fails."""
        from core.downloader import download_file
        dest = os.path.join(tmp_dir, "out.iso")
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.raise_for_status = MagicMock(side_effect=Exception("HTTP 500"))
        mock_resp.headers = {}
        mock_resp.iter_content = MagicMock(return_value=iter([]))
        with patch("requests.get", return_value=mock_resp):
            with pytest.raises(DownloadError):
                download_file("http://example.com/out.iso", dest)
        assert not os.path.exists(dest + ".part")

    def test_checksum_mismatch_raises(self, tmp_dir):
        from core.downloader import download_file
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.raise_for_status = MagicMock()
        mock_response.headers = {"content-length": "5"}
        mock_response.iter_content = MagicMock(return_value=iter([b"hello"]))

        dest = os.path.join(tmp_dir, "test.iso")
        with patch("requests.get", return_value=mock_response):
            with pytest.raises(DownloadError, match="[Cc]hecksum"):
                download_file(
                    "http://example.com/test.iso", dest,
                    checksum="wrong_hash_here",
                    checksum_type="sha256"
                )
