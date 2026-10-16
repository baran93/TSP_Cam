"""On-demand RAM-only Picamera2 preview; no MP4 recording is implemented.

Preview is single-owner. The worker owns the camera only while somebody
is viewing it, then closes it after 15 s. At most 5 JPEG frames per second.
When the recorder lands, frames MUST come from the recorder pipeline,
not a competing second Picamera2 instance.
"""
from __future__ import annotations

import io
import logging
import threading
import time


class PreviewManager:
    def __init__(self, camera_factory=None, clock=time.monotonic, idle_seconds=15, settings=None):
        self._camera_factory = camera_factory
        self._clock = clock
        self._idle_seconds = idle_seconds
        self._settings = settings
        self._lock = threading.Lock()
        self._thread = None
        self._last_request = 0.0
        self._retry_after = 0.0
        self._frame = None
        self._frame_at = 0.0
        self._state = "idle"
        self._error = None
        self._stop = threading.Event()
        self._restart = threading.Event()

    def profile(self):
        from .settings import DEFAULTS
        return self._settings.get() if self._settings is not None else DEFAULTS.copy()

    def change_profile(self):
        """Close active preview and reconfigure with the next request."""
        self._restart.set()

    def request(self):
        now = self._clock()
        with self._lock:
            self._last_request = now
            if (self._thread is None or not self._thread.is_alive()) and now >= self._retry_after:
                self._state = "starting"
                self._error = None
                self._restart.clear()
                self._thread = threading.Thread(target=self._run, name="tspcam-preview", daemon=True)
                self._thread.start()
            return self._fresh_frame(now), self._report(now)

    def snapshot(self):
        with self._lock:
            return self._fresh_frame(self._clock())

    def info(self):
        with self._lock:
            return self._report(self._clock())

    def shutdown(self):
        self._stop.set()
        self._restart.set()
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=5)

    def _fresh_frame(self, now):
        return self._frame if self._frame and now - self._frame_at < 2.0 else None

    def _report(self, now):
        return {"state": self._state,
                "live": self._fresh_frame(now) is not None,
                "age_seconds": round(now - self._frame_at, 2) if self._frame_at else None,
                "error": self._error, "mode": "on_demand_jpeg",
                "profile": self.profile()}

    def _run(self):
        camera = None
        try:
            profile = self.profile()
            width, height = map(int, profile["preview_resolution"].split("x"))
            fps = profile["preview_fps"]
            if self._camera_factory is None:
                from picamera2 import Picamera2
                camera = Picamera2()
            else:
                camera = self._camera_factory()
            config = camera.create_preview_configuration(
                main={"size": (width, height), "format": "RGB888"},
                buffer_count=2,
                controls={"FrameRate": fps},
            )
            camera.configure(config)
            camera.start()
            with self._lock:
                self._state = "running"
                self._frame = None
                self._frame_at = 0.0
            while not self._stop.is_set() and not self._restart.is_set():
                with self._lock:
                    last_request = self._last_request
                if self._clock() - last_request > self._idle_seconds:
                    break
                start = self._clock()
                output = io.BytesIO()
                camera.capture_file(output, format="jpeg")
                jpeg = output.getvalue()
                if not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
                    raise RuntimeError("Invalid JPEG returned by Picamera2")
                with self._lock:
                    self._frame = jpeg
                    self._frame_at = self._clock()
                remaining = max(0.0, (1.0 / fps) - (self._clock() - start))
                if self._stop.wait(remaining):
                    break
        except Exception as exc:
            logging.exception("Camera preview failed; will retry on later request")
            with self._lock:
                self._state = "error"
                self._error = f"{type(exc).__name__}: {str(exc)[:180]}"
                self._frame = None
                self._frame_at = 0.0
                self._retry_after = self._clock() + 10.0
        finally:
            if camera is not None:
                try:
                    camera.stop()
                except Exception:
                    pass
                try:
                    camera.close()
                except Exception:
                    pass
            with self._lock:
                if self._state != "error":
                    self._state = "idle"
                self._frame = None
                self._frame_at = 0.0
