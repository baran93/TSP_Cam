"""LAN technician dashboard, read-only diagnostics and pilot profile controls."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import json

from .config import Config
from .diagnostics import status
from .preview import PreviewManager
from .settings import SettingsStore
from .usb_storage import inspect_usb, save_selection

UI_PATH = Path(__file__).with_name("panel.html")
LOGO_PATH = Path(__file__).with_name("tsp-logo.png")
FALLBACK = b'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#101d2c"/><text x="50%" y="50%" fill="#cbd5e1" font-size="24" font-family="sans-serif" text-anchor="middle">Waiting for camera...</text></svg>'


def make_handler(config: Config, preview: PreviewManager | None = None, settings: SettingsStore | None = None):
    settings = settings or SettingsStore()
    preview = preview or PreviewManager(settings=settings)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, status_code, body, mime, headers=None):
            self.send_response(status_code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, max-age=0")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _json(self, code, data):
            self._send(code, json.dumps(data, sort_keys=True).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/":
                self._send(200, UI_PATH.read_bytes(), "text/html; charset=utf-8")
            elif route == "/assets/tsp-logo.png":
                self._send(200, LOGO_PATH.read_bytes(), "image/png")
            elif route == "/api/status":
                data = status(config)
                data["preview"] = preview.info()
                data["camera_settings"] = settings.get()
                self._json(200, data)
            elif route == "/api/preview.jpg":
                jpg, _ = preview.request()
                self._send(200, jpg if jpg is not None else FALLBACK,
                           "image/jpeg" if jpg is not None else "image/svg+xml",
                           {"X-Preview-Live": "1" if jpg is not None else "0"})
            elif route == "/api/snapshot.jpg":
                jpg = preview.snapshot()
                if jpg is None:
                    self._json(503, {"error": "No recent camera image; open Live View first"})
                    return
                self._send(200, jpg, "image/jpeg",
                           {"Content-Disposition": 'attachment; filename="tspcam-snapshot.jpg"'})
            elif route == "/api/settings":
                self._json(200, settings.get())
            elif route == "/api/storage":
                self._json(200, inspect_usb(config.usb_mount))
            elif route == "/healthz":
                self._json(200, {"service": "ok", "recorder": "not_implemented"})
            else:
                self._json(404, {"error": "Not found"})

        def do_POST(self):
            route = urlsplit(self.path).path
            if route not in ("/api/settings", "/api/storage/select"):
                self._json(404, {"error": "Not found"})
                return
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                self._json(415, {"error": "Expected application/json"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = -1
            if length <= 0 or length > 2048:
                self._json(400, {"error": "Invalid request length"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if route == "/api/storage/select":
                    if not isinstance(payload, dict) or set(payload) != {"volume_id"}:
                        raise ValueError("Expected volume_id only")
                    target_id = payload["volume_id"]
                    disk_info = inspect_usb(config.usb_mount)
                    choices = [v for v in disk_info["volumes"]
                               if v["id"] == target_id and v["selectable"]]
                    if len(choices) != 1:
                        raise ValueError("Volume must be present, supported and have a unique stable ID")
                    save_selection(target_id)
                    self._json(200, {"selected_id": target_id,
                                     "message": "Saved. Mount service will handle this volume on next check.",
                                     "recording_active": False})
                    return
                prior = settings.get()
                result = settings.update(payload)
            except (ValueError, TypeError, OSError, UnicodeError, KeyError) as exc:
                self._json(400, {"error": str(exc)[:160]})
                return
            if prior["preview_resolution"] != result["preview_resolution"] or prior["preview_fps"] != result["preview_fps"]:
                preview.change_profile()
            self._json(200, {"settings": result,
                             "recording_active": False,
                             "recording_resolution_is_future_only": True})

    return Handler


def serve(config: Config) -> None:
    settings = SettingsStore()
    preview = PreviewManager(settings=settings)
    # Pilot-only LAN, no auth. Never expose router port-forwarding.
    with ThreadingHTTPServer(("0.0.0.0", config.web_port), make_handler(config, preview, settings)) as server:
        server.daemon_threads = True
        try:
            server.serve_forever(poll_interval=0.5)
        finally:
            preview.shutdown()
