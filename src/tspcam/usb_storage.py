"""Safe USB-media discovery and optional pilot automount.

Never use the OS SD card, a bind mount, or a merely existing directory
as the recording destination. Detection is read-only; only the separate
root-owned one-shot service may mount an unambiguous genuine USB volume.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

FILESYSTEMS = {"vfat", "exfat", "ext4", "ntfs", "ntfs3"}
SYSTEM_MOUNTS = {"/", "/boot", "/boot/firmware", "/home", "/var", "/usr", "/tmp"}
DEFAULT_MOUNT = Path("/media/tspcam")


def _mounts(node: dict) -> list[str]:
    vals = node.get("mountpoints")
    if isinstance(vals, list):
        return [s for s in vals if isinstance(s, str) and s]
    val = node.get("mountpoint")
    return [val] if isinstance(val, str) and val else []


def enumerate_usb(lsblk_output: dict) -> list[dict]:
    """Select only filesystem partitions or whole disks underneath TRAN=usb."""
    devices = []
    def scan(node, is_usb=False):
        usb = is_usb or node.get("tran") == "usb"
        kind = node.get("type")
        name = node.get("path")
        fs = node.get("fstype")
        if usb and kind in ("part", "disk") and isinstance(name, str) and name.startswith("/dev/") and fs in FILESYSTEMS:
            mounts = _mounts(node)
            if not any(point in SYSTEM_MOUNTS or point.startswith("/boot/") for point in mounts):
                devices.append({
                    "source": name,
                    "filesystem": fs,
                    "label": node.get("label") or None,
                    "uuid": node.get("uuid") or None,
                    "mountpoints": mounts,
                    "read_only": bool(node.get("ro", False)),
                    "size_bytes": node.get("size"),
                })
        for child in node.get("children") or []:
            if isinstance(child, dict):
                scan(child, usb)
    for node in lsblk_output.get("blockdevices") or []:
        if isinstance(node, dict):
            scan(node)
    return devices


def inspect_usb(config_mount: Path, *, lsblk_data: dict | None = None) -> dict:
    """Discover physical USB disks even when mounted elsewhere (or nowhere)."""
    if lsblk_data is None:
        try:
            p = subprocess.run(
                ["lsblk", "-J", "-b", "-o", "PATH,TYPE,TRAN,FSTYPE,MOUNTPOINTS,RO,SIZE,LABEL,UUID"],
                capture_output=True, text=True, timeout=4, check=False,
            )
            if p.returncode:
                raise RuntimeError(p.stderr.strip()[:160] or "lsblk failed")
            lsblk_data = json.loads(p.stdout)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
            return {"detected": False, "mounted": False, "reason": "discovery_error",
                    "detail": str(exc)[:160], "devices": [], "recording_root": None}
    disks = enumerate_usb(lsblk_data)
    # A preferred mount path is trusted only when it belongs to a real USB disk.
    candidates = [d for d in disks if any(os.path.ismount(mp) and Path(mp).is_dir() for mp in d["mountpoints"])]
    preferred = [d for d in candidates if str(config_mount) in d["mountpoints"]]
    preferred += [d for d in candidates if str(DEFAULT_MOUNT) in d["mountpoints"] and d not in preferred]
    if not preferred and len(candidates) == 1:
        preferred = candidates
    if len(preferred) != 1:
        reason = "multiple_usb_volumes" if len(disks) > 1 else ("not_mounted" if disks else "no_usb_storage")
        return {"detected": bool(disks), "mounted": False, "reason": reason,
                "devices": disks, "recording_root": None}
    item = preferred[0]
    mount = str(config_mount) if str(config_mount) in item["mountpoints"] else (
        str(DEFAULT_MOUNT) if str(DEFAULT_MOUNT) in item["mountpoints"] else item["mountpoints"][0]
    )
    try:
        st = os.statvfs(mount)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = max(0, total - st.f_bfree * st.f_frsize)
        writable = bool(not item["read_only"] and not st.f_flag & os.ST_RDONLY and os.access(mount, os.W_OK))
        return {"detected": True, "mounted": True, "source": item["source"],
                "filesystem": item["filesystem"], "label": item["label"],
                "uuid": item["uuid"], "mount_path": mount,
                "recording_root": mount if writable else None,
                "writable": writable, "free_bytes": free, "total_bytes": total,
                "used_bytes": used, "used_percent": round(100 * used / total, 1) if total else None,
                "devices": disks}
    except OSError as exc:
        return {"detected": True, "mounted": False, "reason": "mount_stat_failed",
                "detail": str(exc)[:160], "devices": disks, "recording_root": None}


def ensure_mount(target: Path = DEFAULT_MOUNT) -> str:
    """Root-only pilot automount, never formats or modifies an existing mount."""
    if os.geteuid() != 0:
        return "Mount agent requires root"
    state = inspect_usb(target)
    if state["mounted"]:
        return "USB is already mounted: " + state["mount_path"]
    disks = state["devices"]
    if len(disks) != 1:
        return "No single eligible USB filesystem; leaving storage unchanged"
    disk = disks[0]
    if disk["read_only"]:
        return "USB filesystem is read-only; refusing to mount for recording"
    if disk["mountpoints"]:
        return "USB already has a mount; refusing duplicate mount"
    if not re.fullmatch(r"/dev/[A-Za-z0-9_./-]+", disk["source"]):
        return "Unexpected USB path; refusing"
    if target.is_symlink() or (target.exists() and (not target.is_dir() or any(target.iterdir()))):
        return "Target is not an empty plain directory; refusing"
    target.mkdir(parents=True, exist_ok=True)
    if os.path.ismount(target):
        return "Target already mounted"
    options = ["nosuid", "nodev", "noexec", "rw"]
    if disk["filesystem"] in {"vfat", "exfat", "ntfs", "ntfs3"}:
        import pwd
        identity = pwd.getpwnam("tspcam")
        options.extend([f"uid={identity.pw_uid}", f"gid={identity.pw_gid}", "umask=0022"])
    try:
        p = subprocess.run(["mount", "-o", ",".join(options), "--",
                            disk["source"], str(target)], capture_output=True, text=True, timeout=12, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "Mount failed: " + str(exc)[:160]
    if p.returncode:
        return "Mount failed: " + p.stderr.strip()[:200]
    return "Mounted " + disk["source"] + " on " + str(target)


def main() -> int:
    result = ensure_mount()
    print("TSP_Cam USB: " + result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
