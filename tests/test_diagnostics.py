import unittest
from pathlib import Path
from unittest.mock import patch

from tspcam.config import Config
from tspcam.diagnostics import mounted_volume, status


class DiagnosticTests(unittest.TestCase):
    def test_directory_is_not_evidence_of_mount(self):
        self.assertEqual(mounted_volume(Path("/media/tspcam"), ""), {"mounted": False, "reason": "not_mounted"})

    def test_tmpfs_is_not_usb(self):
        table = "22 1 0:25 / /media/tspcam rw,nosuid - tmpfs tmpfs rw\n"
        actual = mounted_volume(Path("/media/tspcam"), table)
        self.assertEqual(actual["reason"], "unsupported_mount_source")

    def test_usb_mount_detected(self):
        table = "22 1 8:1 / /media/tspcam rw,relatime - exfat /dev/sda1 rw\n"
        with patch("tspcam.diagnostics.os.statvfs") as fake:
            fake.return_value.f_bavail = 100
            fake.return_value.f_frsize = 4096
            result = mounted_volume(Path("/media/tspcam"), table)
        self.assertEqual(result["source"], "/dev/sda1")
        self.assertEqual(result["free_bytes"], 409600)

    def test_no_fake_recorder_status(self):
        out = status(Config())
        self.assertIs(out["recorder_implemented"], False)
        self.assertEqual(out["phase"], "foundation_only")


if __name__ == "__main__":
    unittest.main()
