import pytest
from unittest.mock import patch, MagicMock
import timey_gui


class TestFindLibfaketime:
    def test_found_via_ldconfig(self):
        ldconfig_output = "libfaketime.so.1 (libc6,x86-64) => /usr/lib/x86_64-linux-gnu/libfaketime.so.1\n"
        with patch("timey_gui.subprocess.run") as mock_run, \
             patch("timey_gui.os.path.isfile", return_value=True):
            mock_run.return_value = MagicMock(stdout=ldconfig_output, returncode=0)
            result = timey_gui.find_libfaketime()
        assert result == "/usr/lib/x86_64-linux-gnu/libfaketime.so.1"

    def test_ldconfig_stale_path_falls_through_to_glob(self):
        """ldconfig returns a path that doesn't exist on disk — falls through to glob."""
        ldconfig_output = "libfaketime.so.1 (libc6,x86-64) => /stale/path/libfaketime.so.1\n"
        with patch("timey_gui.subprocess.run") as mock_run, \
             patch("timey_gui.os.path.isfile", side_effect=lambda p: p == "/usr/lib/libfaketime.so.1"), \
             patch("timey_gui.glob.glob", return_value=["/usr/lib/libfaketime.so.1"]):
            mock_run.return_value = MagicMock(stdout=ldconfig_output, returncode=0)
            result = timey_gui.find_libfaketime()
        assert result == "/usr/lib/libfaketime.so.1"

    def test_found_via_glob_fallback(self):
        """ldconfig finds nothing; glob finds the .so."""
        with patch("timey_gui.subprocess.run") as mock_run, \
             patch("timey_gui.glob.glob", return_value=["/usr/local/lib/libfaketime.so.1"]), \
             patch("timey_gui.os.path.isfile", return_value=True):
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = timey_gui.find_libfaketime()
        assert result == "/usr/local/lib/libfaketime.so.1"

    def test_not_found_returns_none(self):
        with patch("timey_gui.subprocess.run") as mock_run, \
             patch("timey_gui.glob.glob", return_value=[]), \
             patch("timey_gui.os.path.isfile", return_value=False):
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            result = timey_gui.find_libfaketime()
        assert result is None
