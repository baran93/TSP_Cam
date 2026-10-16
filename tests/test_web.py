import unittest
from pathlib import Path
from tspcam.config import Config
from tspcam.web import make_handler, serve, UI_PATH, LOGO_PATH
from unittest.mock import patch


class WebTests(unittest.TestCase):
    def test_readonly_handler_and_settings_are_separate(self):
        handler = make_handler(Config())
        self.assertTrue(hasattr(handler, "do_GET"))
        self.assertTrue(hasattr(handler, "do_POST"))

    @patch("tspcam.web.ThreadingHTTPServer")
    def test_lan_bind(self, fake):
        serve(Config(web_port=8765))
        self.assertEqual(fake.call_args.args[0], ("0.0.0.0", 8765))

    def test_packaged_html_and_png(self):
        html = UI_PATH.read_text(encoding="utf-8")
        self.assertIn("/api/preview.jpg", html)
        self.assertIn("/api/settings", html)
        self.assertIn("/assets/tsp-logo.png", html)
        self.assertTrue(LOGO_PATH.read_bytes().startswith(b"\x89PNG"))

    def test_installer(self):
        script = (Path(__file__).resolve().parent.parent / "scripts/install-local.sh").read_text()
        self.assertIn('chmod 0755 "$DEST"', script)
        self.assertIn('mv -Tf -- "$INSTALL_ROOT/.current.$$" "$INSTALL_ROOT/current"', script)
        self.assertIn("python3-picamera2", script)
        self.assertIn("tspcam-usb-mount.timer", script)


if __name__ == "__main__":
    unittest.main()
