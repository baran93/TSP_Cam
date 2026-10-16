import os
from pathlib import Path
import tempfile
import unittest

from tspcam.config import Config, load_config


class ConfigTests(unittest.TestCase):
    def test_missing_file_returns_defaults(self):
        self.assertEqual(load_config(Path("/nonexistent/tspcam/testing/config.toml")), Config())

    def test_valid_config(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "config.toml"
            f.write_text('box_id="TSP_Box_004"\nusb_mount="/media/usb0"\ntimezone="Europe/London"\nweb_port=9000\n')
            conf = load_config(f)
            self.assertEqual(conf.box_id, "TSP_Box_004")
            self.assertEqual(conf.web_port, 9000)

    def test_reject_root_usb_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "config.toml"
            f.write_text('usb_mount="/"\n')
            with self.assertRaises(ValueError):
                load_config(f)
            f.write_text('bad_key="x"\n')
            with self.assertRaises(ValueError):
                load_config(f)

    def test_reject_bool_as_port(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "config.toml"
            f.write_text("web_port=true\n")
            with self.assertRaises(ValueError):
                load_config(f)


if __name__ == "__main__":
    unittest.main()
