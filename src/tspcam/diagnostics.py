"""Non-invasive diagnostics. Never assumes an existing directory is a USB mount."""
from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
import time

from . import __version__
from .config import Config


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return None


def mounted_volume(mount: Path, mountinfo: str | None = None) -> dict:
    """Check the kernel mount table, not merely Path.exists()/is_dir()."""
    if mountinfo is None:
        mountinfo = _read("/proc/self/mountinfo") or ""
    wanted = str(mount.resolve(strict=False))
    for line in mountinfo.splitlines():
        try:
            before, after = line.split(" - ", 1)
            fields = before.split()
            mount_at = fields[4].replace(r"\040", " ").replace(r"\011", "\t")
            source_fields = after.split()
            filesystem, source = source_fields[:2]
            if mount_at != wanted:
                continue
            # A non-/dev volume may be a network share, tmpfs or bind mount;
            # treat it as unsupported for this initial recorder.
            if not source.startswith("/dev/"):
                return {"mounted": False, "reason": "unsupported_mount_source", "source": source}
            try:
                size = os.statvfs(mount)
                free = size.f_bavail * size.f_frsize
            except OSError:
                return {"mounted": False, "reason": "statvfs_failed", "source": source}
            return {"mounted": True, "source": source, "filesystem": filesystem, "free_bytes": free}
        except (ValueError, IndexError):
            continue
    return {"mounted": False, "reason": "not_mounted"}


def rtc_overview() -> list[dict]:
    root = Path("/sys/class/rtc")
    try:
        devices = sorted(root.glob("rtc*"))
    except OSError:
        return []
    return [{"device": p.name, "name": _read(str(p / "name")) or "unknown",
             "date": _read(str(p / "date")), "time": _read(str(p / "time"))}
            for p in devices]


def cpu_temperature() -> float | None:
    value = _read("/sys/class/thermal/thermal_zone0/temp")
    try:
        return round(int(value) / 1000.0, 1) if value else None
    except ValueError:
        return None


def _uptime() -> int | None:
    value = _read("/proc/uptime")
    try:
        return int(float(value.split()[0])) if value else None
    except (ValueError, IndexError):
        return None


def throttling() -> str | None:
    try:
        p = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def status(config: Config) -> dict:
    """Read-only: this is not proof of a running recorder or healthy footage."""
    return {
        "version": __version__,
        "phase": "foundation_only",
        "recorder_implemented": False,
        "box_id": config.box_id,
        "hostname": platform.node(),
        "machine": platform.machine(),
        "timezone_configured": config.timezone,
        "uptime_seconds": _uptime(),
        "cpu_temperature_c": cpu_temperature(),
        "throttled": throttling(),
        "usb": mounted_volume(config.usb_mount),
        "rtc_devices": rtc_overview(),
        "time_unix": int(time.time()),
    }
