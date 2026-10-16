import unittest
from tspcam.config import Config
from tspcam.web import make_handler


class WebTests(unittest.TestCase):
    def test_readonly_panel_handler_exists(self):
        handler = make_handler(Config())
        self.assertTrue(callable(handler))
        self.assertTrue(hasattr(handler, "do_GET"))
        self.assertFalse(hasattr(handler, "do_POST"))


if __name__ == "__main__":
    unittest.main()
