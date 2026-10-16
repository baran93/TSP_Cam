import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from tspcam.usb_storage import enumerate_usb, inspect_usb, ensure_mount


def volume(mount=None, filesystem="exfat", connection="usb"):
    return {"blockdevices": [{"path": "/dev/sda", "type": "disk", "tran": connection,
                "children": [{"path": "/dev/sda1", "type": "part", "fstype": filesystem,
                              "mountpoints": [mount], "ro": False, "label": "USB", "size": 10000}]}]}


class USBStorageTests(unittest.TestCase):
    def test_detects_unmounted_usb_and_does_not_select_sd(self):
        state = inspect_usb(Path("/media/tspcam"), lsblk_data=volume())
        self.assertTrue(state["detected"])
        self.assertFalse(state["mounted"])
        self.assertIsNone(state["recording_root"])

    def test_rejects_sd_even_if_mounted_at_usb_path(self):
        state = inspect_usb(Path("/media/tspcam"), lsblk_data=volume("/media/tspcam", connection=None))
        self.assertFalse(state["detected"])
        self.assertIsNone(state["recording_root"])

    @patch("tspcam.usb_storage.os.path.ismount", return_value=True)
    @patch("tspcam.usb_storage.os.access", return_value=True)
    @patch("tspcam.usb_storage.os.statvfs")
    def test_detects_usb_at_usb0(self, statvfs, access, ismount):
        statvfs.return_value = MagicMock(f_blocks=1000, f_frsize=1024, f_bavail=400, f_bfree=400, f_flag=0)
        state = inspect_usb(Path("/media/tspcam"), lsblk_data=volume("/media/usb0"))
        self.assertEqual(state["recording_root"], "/media/usb0")
        self.assertEqual(state["source"], "/dev/sda1")
        self.assertEqual(state["used_percent"], 60.0)

    @patch("tspcam.usb_storage.os.path.ismount", return_value=True)
    @patch("tspcam.usb_storage.os.access", return_value=True)
    @patch("tspcam.usb_storage.os.statvfs")
    def test_refuses_multiple_usb_mounts_as_ambiguous(self, statvfs, access, ismount):
        data = volume("/media/a")
        data["blockdevices"][0]["children"].append({
            "path":"/dev/sda2", "type":"part", "fstype":"exfat",
            "mountpoints":["/media/b"], "ro":False})
        state = inspect_usb(Path("/media/tspcam"), lsblk_data=data)
        self.assertFalse(state["mounted"])
        self.assertEqual(state["reason"], "multiple_usb_volumes")

    @patch("tspcam.usb_storage.os.geteuid", return_value=1000)
    def test_mount_requires_root(self, uid):
        self.assertEqual(ensure_mount(), "Mount agent requires root")


if __name__ == "__main__":
    unittest.main()
