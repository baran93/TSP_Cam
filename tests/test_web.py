import unittest
from pathlib import Path
from unittest.mock import patch
from tspcam.config import Config
from tspcam.web import make_handler, serve


class WebTests(unittest.TestCase):
    def test_readonly_panel_handler_exists(self):
        handler = make_handler(Config())
        self.assertTrue(callable(handler))
        self.assertTrue(hasattr(handler, "do_GET"))
        self.assertFalse(hasattr(handler, "do_POST"))

    @patch("tspcam.web.ThreadingHTTPServer")
    def test_lan_bind_for_pilot(self, fake):
        serve(Config(web_port=8765))
        self.assertEqual(fake.call_args.args[0], ("0.0.0.0", 8765))

    def test_installer_release_permissions_and_symlink_name(self):
        script = (Path(__file__).resolve().parent.parent / "scripts/install-local.sh").read_text()
        self.assertIn('chmod 0755 "$DEST"', script)
        self.assertIn('mv -Tf -- "$INSTALL_ROOT/.current.$" "$INSTALL_ROOT/current"', script)


if __name__ == "__main__":
    unittest.main()
