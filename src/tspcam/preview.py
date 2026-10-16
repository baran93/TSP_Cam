"""On-demand, in-memory camera preview for the pre-recorder hardware pilot.

A single Picamera2 instance captures JPEG frames only while somebody requests
the web preview. When no clients poll, close the camera promptly to save power.
Do not import Picamera2 when the module loads (CI/ordinary PCs lack libcamera).
Do not touch the recording USB/SD. This module must be replaced by shared
recorder-owned frames when the production H264 capture process is implemented.
"""
from __future__ import annotations

import io
import logging
import threading
import time


class PreviewManager:
    def __init__(self, camera_factory=None, clock=time.monotonic, idle_seconds=15):
        self._camera_factory = camera_factory
        self._clock = clock
        self._idle_seconds = idle_seconds
        self._lock = threading.Lock()
        self._thread = None
        self._last_request = 0.0
        self._retry_after = 0.0
        self._frame = None
        self._frame_at = 0.0
        self._state = "idle"
        self._error = None
        self._stop = threading.Event()

    def request(self):
        """Return (JPEG bytes or None, state dict). Nonblocking for web threads."""
        now = self._clock()
        with self._lock:
            self._last_request = now
            if (self._thread is None or not self._thread.is_alive()) and now >= self._retry_after:
                self._state = "starting"
                self._error = None
                self._thread = threading.Thread(
                    target=self._run, name="tspcam-preview", daemon=True
                )
                self._thread.start()
            return self._fresh_frame(now), self._report(now)

    def snapshot(self):
        """Read last frame without starting the camera or refreshing client timeout."""
        with self._lock:
            return self._fresh_frame(self._clock())

    def info(self):
        with self._lock:
            return self._report(self._clock())

    def shutdown(self):
        self._stop.set()
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout=4)

    def _fresh_frame(self, now):
        # Never serve an old shot as though it were a live camera frame.
        return self._frame if self._frame and now - self._frame_at < 4.0 else None

    def _report(self, now):
        return {
            "state": self._state,
            "live": self._fresh_frame(now) is not None,
            "age_seconds": round(now - self._frame_at, 1) if self._frame_at else None,
            "error": self._error,
            "mode": "on_demand_jpeg_1fps",
        }

    def _run(self):
        camera = None
        try:
            if self._camera_factory is None:
                from picamera2 import Picamera2  # import only when preview is requested
                camera = Picamera2()
            else:
                camera = self._camera_factory()
            config = camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                buffer_count=2,
            )
            camera.configure(config)
            camera.start()
            with self._lock:
                self._state = "running"
            while not self._stop.is_set():
                with self._lock:
                    last_request = self._last_request
                if self._clock() - last_request > self._idle_seconds:
                    break
                output = io.BytesIO()
                camera.capture_file(output, format="jpeg")
                jpeg = output.getvalue()
                if not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
                    raise RuntimeError("Picamera2 did not produce a complete JPEG")
                with self._lock:
                    self._frame = jpeg
                    self._frame_at = self._clock()
                if self._stop.wait(1.0):
                    break
        except Exception as exc:  # bad sensor/connector/driver must NOT stop web dashboard
            logging.exception("Camera preview failed; retry on future request")
            with self._lock:
                self._state = "error"
                self._error = f"{type(exc).__name__}: {str(exc)[:180]}"
                self._frame = None
                self._frame_at = 0.0
                self._retry_after = self._clock() + 20.0
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
