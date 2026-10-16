import unittest
from unittest.mock import Mock

from tspcam.preview import PreviewManager


class PreviewTests(unittest.TestCase):
    def test_no_camera_is_opened_until_client_requests_it(self):
        camera = Mock()
        manager = PreviewManager(camera_factory=lambda: camera)
        self.assertEqual(manager.info()["state"], "idle")
        self.assertFalse(camera.called)
        self.assertIsNone(manager.snapshot())

    def test_stale_frame_is_not_served_as_live(self):
        manager = PreviewManager(clock=lambda: 100.0)
        manager._frame = b"JPEG DATA"
        manager._frame_at = 90.0
        self.assertIsNone(manager.snapshot())
        self.assertFalse(manager.info()["live"])

    def test_fresh_frame_is_available_for_snapshot(self):
        manager = PreviewManager(clock=lambda: 100.0)
        manager._frame = b"JPEG DATA"
        manager._frame_at = 98.0
        self.assertEqual(manager.snapshot(), b"JPEG DATA")
        self.assertTrue(manager.info()["live"])


if __name__ == "__main__":
    unittest.main()
