"""Read-only pilot dashboard over connected interfaces, without auth (pilot only)."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json

from .config import Config
from .diagnostics import status

INDEX = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TSP_Cam · Phase 0</title>
<style>body{font:16px system-ui;background:#101820;color:#fff;margin:0 auto;padding:24px;max-width:650px}
header{display:flex;align-items:center;gap:12px}span{color:#a8bdc9}pre{white-space:pre-wrap;word-wrap:break-word;
background:#1c2b35;padding:18px;border-radius:12px}small{color:#ffce74}</style>
<header><h1>TSP_Cam</h1><span>Foundation · Phase 0</span></header>
<p>This dashboard currently provides read-only hardware diagnostics.</p>
<small>Recording and remote camera controls are NOT implemented yet.</small><pre id="data">Loading…</pre>
<script>async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});
if(!r.ok)throw Error('HTTP '+r.status);document.getElementById('data').textContent=
JSON.stringify(await r.json(),null,2)}catch(e){document.getElementById('data').textContent=
'Error: '+e.message}}refresh();setInterval(refresh,15000)</script></html>"""


def make_handler(config: Config):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                body = INDEX.encode("utf-8")
                content_type = "text/html; charset=utf-8"
            elif self.path == "/api/status":
                body = json.dumps(status(config), sort_keys=True).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif self.path == "/healthz":
                body = b'{"service":"ok","recorder":"not_implemented"}'
                content_type = "application/json; charset=utf-8"
            else:
                self.send_error(404, "Not found")
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)
    return Handler


def serve(config: Config) -> None:
    # PILOT ONLY: all LAN interfaces, no auth or TLS.
    # Never publish router port forwarding to this service.
    with ThreadingHTTPServer(("0.0.0.0", config.web_port), make_handler(config)) as server:
        server.serve_forever(poll_interval=0.5)
