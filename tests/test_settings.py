import tempfile
import unittest
from pathlib import Path
from tspcam.settings import DEFAULTS, SettingsStore


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            store = SettingsStore(Path(temp) / "settings.json")
            self.assertEqual(store.get(), DEFAULTS)

    def test_persistence_and_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            store = SettingsStore(path)
            store.update({"preview_fps": 3, "preview_resolution": "800x600"})
            self.assertEqual(SettingsStore(path).get()["preview_fps"], 3)
            with self.assertRaises(ValueError):
                store.update({"preview_fps": 99})
            with self.assertRaises(ValueError):
                store.update({"recording_resolution": "../secret"})
            with self.assertRaises(ValueError):
                store.update({"preview_fps": True})
            self.assertEqual(SettingsStore(path).get()["preview_fps"], 3)


if __name__ == "__main__":
    unittest.main()
