"""Lightweight responsive read-only TSP_Cam pilot panel and on-demand preview."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json

from .config import Config
from .diagnostics import status
from .preview import PreviewManager

UI_PATH = Path(__file__).with_name("panel.html")
FALLBACK = b'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#101d2c"/><text x="50%" y="50%" fill="#cbd5e1" font-size="24" font-family="sans-serif" text-anchor="middle">Waiting for camera...</text></svg>'


def make_handler(config: Config, preview: PreviewManager | None = None):
    preview = preview or PreviewManager()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlsplit(self.path).path
            headers = {}
            if route == "/":
                body = UI_PATH.read_bytes()
                mime = "text/html; charset=utf-8"
            elif route == "/api/status":
                data = status(config)
                data["preview"] = preview.info()
                data["usb"]["mount_path"] = str(config.usb_mount)
                body = json.dumps(data, sort_keys=True).encode("utf-8")
                mime = "application/json; charset=utf-8"
            elif route == "/api/preview.jpg":
                jpg, _ = preview.request()
                body = jpg if jpg is not None else FALLBACK
                mime = "image/jpeg" if jpg is not None else "image/svg+xml"
                headers["X-Preview-Live"] = "1" if jpg is not None else "0"
            elif route == "/api/snapshot.jpg":
                jpg = preview.snapshot()
                if jpg is None:
                    self.send_error(503, "No fresh camera frame")
                    return
                body = jpg
                mime = "image/jpeg"
                headers["Content-Disposition"] = 'attachment; filename="tspcam-snapshot.jpg"'
            elif route == "/healthz":
                body = b'{"service":"ok","recorder":"not_implemented"}'
                mime = "application/json; charset=utf-8"
            else:
                self.send_error(404, "Not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    return Handler


def serve(config: Config) -> None:
    preview = PreviewManager()
    # Pilot only: all LAN interfaces, no auth/TLS, no router port forwarding.
    with ThreadingHTTPServer(("0.0.0.0", config.web_port), make_handler(config, preview)) as server:
        server.daemon_threads = True
        try:
            server.serve_forever(poll_interval=0.5)
        finally:
            preview.shutdown()
