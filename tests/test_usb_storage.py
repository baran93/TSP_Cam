"""USB detection and selection behaviour without touching hardware or disks."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from tspcam.usb_storage import (
    inspect_usb, volume_inventory, save_selection, selected_id,
    ensure_mount, WRITE_FORMATS, _selected
)


def usb_disk(letter, *, fs="exfat", uuid=None, mount=None, label=None, tran="usb"):
    uuid = uuid or f"1111-2222-{letter}"
    return {
        "name": f"sd{letter}", "path": f"/dev/sd{letter}", "type": "disk",
        "tran": tran, "hotplug": 1, "model": f"USB-{letter.upper()}",
        "children": [{
            "name": f"sd{letter}1", "path": f"/dev/sd{letter}1",
            "type": "part", "fstype": fs, "uuid": uuid, "partuuid": f"aabbccdd-{letter}",
            "mountpoints": [mount], "size": 8_000_000_000, "ro": False,
            "label": label or f"DATA_{letter}"
        }],
    }


class USBTests(unittest.TestCase):
    def test_one_usb_volume_automatic_selection(self):
        state = inspect_usb(lsblk_data={"blockdevices": [usb_disk("a")]}, choice="")
        self.assertTrue(state["detected"])
        self.assertEqual(state["selection_mode"], "automatic_single")
        self.assertFalse(state["mounted"])
        self.assertEqual(state["source"], "/dev/sda1")
        self.assertEqual(state["reason"], "selected_not_mounted")
        self.assertIsNone(state["recording_root"])

    def test_multiple_usb_volumes_must_be_selected(self):
        data = {"blockdevices": [usb_disk("a"), usb_disk("b")]}
        state = inspect_usb(lsblk_data=data, choice="")
        self.assertEqual(state["reason"], "choose_volume")
        self.assertEqual(len(state["volumes"]), 2)
        self.assertIsNone(state["recording_root"])
        self.assertIn("DATA_a", [v["display_name"] for v in state["volumes"]])
        self.assertEqual(state["volumes"][1]["filesystem"], "exfat")

    def test_selected_uuid_stays_the_same_if_device_path_changes(self):
        data = {"blockdevices": [usb_disk("a", uuid="ABC-1"), usb_disk("b", uuid="ABC-2")]}
        result = inspect_usb(lsblk_data=data, choice="uuid:ABC-2")
        self.assertEqual(result["source"], "/dev/sdb1")
        after_swap = {"blockdevices": [usb_disk("a", uuid="ABC-2"), usb_disk("b", uuid="ABC-1")]}
        result = inspect_usb(lsblk_data=after_swap, choice="uuid:ABC-2")
        self.assertEqual(result["source"], "/dev/sda1")

    def test_selected_missing_does_not_fall_back(self):
        data = {"blockdevices": [usb_disk("a")]}
        state = inspect_usb(lsblk_data=data, choice="uuid:unknown")
        self.assertEqual(state["selection_mode"], "selected_missing_or_duplicate")
        self.assertIsNone(state["recording_root"])

    def test_duplicate_uuid_prevents_selection(self):
        data = {"blockdevices": [usb_disk("a", uuid="same"), usb_disk("b", uuid="same")]}
        state = inspect_usb(lsblk_data=data, choice="uuid:same")
        self.assertEqual(state["selection_mode"], "selected_missing_or_duplicate")

    def test_sd_root_is_not_candidate(self):
        sd = {"name": "mmcblk0", "path": "/dev/mmcblk0", "type": "disk",
              "tran": None, "children": [{"path": "/dev/mmcblk0p2", "type": "part",
                                          "fstype": "ext4", "mountpoints": ["/"]}]}
        state = inspect_usb(lsblk_data={"blockdevices": [sd]}, choice="")
        self.assertFalse(state["detected"])
        self.assertEqual(state["reason"], "no_usb_volume")

    def test_hotplug_disk_with_missing_transport(self):
        state = inspect_usb(lsblk_data={"blockdevices": [usb_disk("a", tran=None)]}, choice="")
        self.assertTrue(state["detected"])

    def test_unsupported_filesystems_still_appear(self):
        data = {"blockdevices": [usb_disk("a", fs="apfs"), usb_disk("b", fs="iso9660"),
                                 usb_disk("c", fs=None)]}
        state = inspect_usb(lsblk_data=data, choice="")
        self.assertEqual(len(state["volumes"]), 3)
        self.assertTrue(all(not v["selectable"] for v in state["volumes"]))
        self.assertEqual(state["reason"], "choose_volume")

    def test_common_writable_formats_are_known(self):
        for fs in ("vfat", "exfat", "ntfs", "ext2", "ext3", "ext4", "xfs", "btrfs", "f2fs"):
            with self.subTest(fs=fs):
                volumes, _ = volume_inventory({"blockdevices": [usb_disk("a", fs=fs)]})
                self.assertTrue(volumes[0]["supported"])

    def test_mount_selection_persists_as_stable_id(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "selected-volume.json"
            save_selection("uuid:ABCD-1234", choice_path=path)
            self.assertEqual(selected_id(path), "uuid:ABCD-1234")
            with self.assertRaises(ValueError):
                save_selection("../../../etc/passwd", choice_path=path)

    @patch("tspcam.usb_storage.os.path.ismount", return_value=True)
    @patch("tspcam.usb_storage.Path.is_dir", return_value=True)
    @patch("tspcam.usb_storage.os.access", return_value=True)
    @patch("tspcam.usb_storage.os.statvfs")
    def test_mounted_volume_usable_as_recorder_target(self, statvfs, access, is_dir, is_mount):
        statvfs.return_value = MagicMock(
            f_blocks=1000, f_frsize=4096, f_bfree=600,
            f_bavail=550, f_flag=0
        )
        data = {"blockdevices": [usb_disk("a", mount="/media/usb0")]}
        state = inspect_usb(lsblk_data=data, choice="")
        self.assertEqual(state["mount_path"], "/media/usb0")
        self.assertTrue(state["writable"])
        self.assertIn(state["recording_root"],
                      ("/media/usb0", "/media/usb0/TSP_Cam"))

    @patch("tspcam.usb_storage.os.geteuid", return_value=1000)
    def test_mount_requires_root(self, fake):
        self.assertEqual(ensure_mount(), "root required")


if __name__ == "__main__":
    unittest.main()
