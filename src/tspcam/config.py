"""Typed, read-only configuration. Never write to the recording volume."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib


@dataclass(frozen=True)
class Config:
    box_id: str = "UNASSIGNED"
    usb_mount: Path = Path("/media/tspcam")
    timezone: str = "Europe/London"
    web_port: int = 8765


def load_config(path: Path | None = None) -> Config:
    path = path or Path(os.environ.get("TSPCAM_CONFIG", "/etc/tspcam/config.toml"))
    if not path.is_file():
        return Config()
    with path.open("rb") as stream:
        payload = tomllib.load(stream)
    if not isinstance(payload, dict):
        raise ValueError("Configuration must be a TOML table")
    allowed = {"box_id", "usb_mount", "timezone", "web_port"}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError("Unknown configuration keys: " + ", ".join(sorted(unknown)))
    box_id = payload.get("box_id", "UNASSIGNED")
    mount = payload.get("usb_mount", "/media/tspcam")
    timezone = payload.get("timezone", "Europe/London")
    web_port = payload.get("web_port", 8765)
    if not isinstance(box_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", box_id):
        raise ValueError("Invalid box_id")
    if not isinstance(mount, str) or not mount.startswith("/"):
        raise ValueError("usb_mount must be an absolute path")
    if ".." in Path(mount).parts or Path(mount) == Path("/"):
        raise ValueError("unsafe usb_mount")
    if not isinstance(timezone, str) or not re.fullmatch(r"[A-Za-z0-9_+/-]{1,90}", timezone):
        raise ValueError("Invalid timezone")
    if type(web_port) is not int or not (1024 <= web_port <= 65535):
        raise ValueError("web_port must be an integer between 1024 and 65535")
    return Config(box_id=box_id, usb_mount=Path(mount), timezone=timezone, web_port=web_port)
