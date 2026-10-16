"""Persistent, validated pilot camera settings. Recorder profile is future-only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import threading

DEFAULT_PATH = Path("/var/lib/tspcam/settings.json")
PREVIEW_SIZES = {"640x480", "800x600", "1280x720"}
PREVIEW_FPS = {1, 3, 5}
RECORDING_SIZES = {"800x600", "1280x720", "1280x960", "1920x1080"}
DEFAULTS = {
    "preview_resolution": "640x480",
    "preview_fps": 5,
    "recording_resolution": "800x600",
}


def validate(settings: dict) -> dict:
    if not isinstance(settings, dict) or set(settings) != set(DEFAULTS):
        raise ValueError("Missing or extra camera profile keys")
    if settings["preview_resolution"] not in PREVIEW_SIZES:
        raise ValueError("Unsupported preview resolution")
    if type(settings["preview_fps"]) is not int or settings["preview_fps"] not in PREVIEW_FPS:
        raise ValueError("Unsupported preview FPS")
    if settings["recording_resolution"] not in RECORDING_SIZES:
        raise ValueError("Unsupported recorder resolution")
    return settings.copy()


class SettingsStore:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.data = self._read()

    def _read(self):
        try:
            value = json.loads(self.path.read_text("utf-8"))
            return validate(value)
        except FileNotFoundError:
            return DEFAULTS.copy()
        except (ValueError, OSError, UnicodeError):
            # Invalid stored settings must never crash a camera status panel.
            return DEFAULTS.copy()

    def get(self):
        with self.lock:
            return self.data.copy()

    def update(self, changes):
        if not isinstance(changes, dict) or set(changes) - set(DEFAULTS):
            raise ValueError("Unrecognized camera setting")
        with self.lock:
            updated = validate({**self.data, **changes})
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=".settings-", dir=self.path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(updated, stream, sort_keys=True)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(name, 0o600)
                os.replace(name, self.path)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
            self.data = updated
            return updated.copy()
