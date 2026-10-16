"""USB volume inventory, user selection and conservative mount service.

Devices from USB transport ONLY; no SD fallback. Discover any filesystem,
offer recording only on compatible read/write Linux filesystems. Stable
UUID/PARTUUID choices survive /dev/sda/b reassignment; ambiguous ids refuse.
No formatting, filesystem repairs, unmounting or deletion is performed.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

# Writable formats depend on installed kernel/helper support.
# Other types are still shown on the UI (read-only or driver unavailable).
WRITE_FORMATS = {"vfat", "fat", "fat32", "exfat", "ext2", "ext3", "ext4",
                 "ntfs", "ntfs3", "fuseblk", "xfs", "btrfs", "f2fs"}
MOUNT_ROOT = Path("/media/tspcam-volumes")
CHOICE_PATH = Path("/var/lib/tspcam/selected-volume.json")
TIMEOUT = 7
SYSTEM_MOUNTS = {"/", "/boot", "/boot/firmware", "/home", "/usr", "/var", "/tmp"}
SAFE_ID = re.compile(r"^(uuid|partuuid):[A-Za-z0-9._:-]{1,128}$")


def mountpoints(node):
    value = node.get("mountpoints")
    if isinstance(value, list):
        return [s for s in value if isinstance(s, str) and s]
    point = node.get("mountpoint")
    return [point] if isinstance(point, str) and point else []


def _usb_root(node):
    """USB bus transport, or removable/hotplug SCSI disk, not SD mmcblk."""
    name = node.get("path") or ""
    return node.get("tran") == "usb" or (
        isinstance(name, str) and bool(re.fullmatch(r"/dev/sd[a-z]+", name))
        and node.get("hotplug") in (True, 1, "1")
    )


def _id(node):
    uuid = node.get("uuid")
    partuuid = node.get("partuuid")
    for kind, value in (("uuid", uuid), ("partuuid", partuuid)):
        if isinstance(value, str) and SAFE_ID.fullmatch(f"{kind}:{value}"):
            return f"{kind}:{value}"
    return None


def volume_inventory(data):
    """Visible entries include unsupported/blank volumes for diagnostics."""
    volumes = []
    hardware = []

    def visit(node, usb=False, disk_meta=None):
        path = node.get("path")
        is_disk = node.get("type") == "disk"
        usb = usb or (is_disk and _usb_root(node))
        if not usb:
            return
        if is_disk:
            disk_meta = {"device": path, "model": node.get("model"),
                         "vendor": node.get("vendor"),
                         "serial": node.get("serial"),
                         "size_bytes": node.get("size")}
            hardware.append(disk_meta)
        children = [x for x in node.get("children") or [] if isinstance(x, dict)]
        # For a partitioned disk: show each partition, not partition-table only.
        if node.get("type") == "part" or (is_disk and not children):
            if not isinstance(path, str) or not path.startswith("/dev/"):
                return
            points = mountpoints(node)
            if any(p in SYSTEM_MOUNTS or p.startswith("/boot/") for p in points):
                return
            fs = (node.get("fstype") or "").lower()
            supported = fs in WRITE_FORMATS
            volumes.append({
                "id": _id(node), "source": path, "label": node.get("label") or "",
                "filesystem": fs or None, "partuuid": node.get("partuuid"),
                "uuid": node.get("uuid"), "size_bytes": node.get("size"),
                "mountpoints": points, "read_only": bool(node.get("ro")),
                "supported": supported, "disk": disk_meta,
                "reason": None if supported else ("missing_filesystem" if not fs else "unsupported_filesystem"),
            })
        for child in children:
            visit(child, usb, disk_meta)

    for item in data.get("blockdevices") or []:
        if isinstance(item, dict):
            visit(item)
    return volumes, hardware


def scan():
    try:
        # --tree prevents flattened lsblk JSON, where partitions silently vanished.
        p = subprocess.run([
            "lsblk", "--json", "--bytes", "--tree",
            "--output", "NAME,PATH,TYPE,TRAN,HOTPLUG,FSTYPE,MOUNTPOINTS,RO,SIZE,LABEL,UUID,PARTUUID,MODEL,VENDOR,SERIAL"
        ], capture_output=True, text=True, timeout=TIMEOUT, check=False)
        if p.returncode:
            raise RuntimeError((p.stderr or "lsblk failed")[:180])
        return json.loads(p.stdout), None
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)[:180]


def selected_id(path=CHOICE_PATH):
    try:
        data = json.loads(Path(path).read_text("utf-8"))
        value = data.get("volume_id")
        return value if isinstance(value, str) and SAFE_ID.fullmatch(value) else None
    except (OSError, ValueError, AttributeError):
        return None


def save_selection(volume_id, *, choice_path=CHOICE_PATH):
    """HTTP code verifies volume is actually in present inventory first."""
    if not isinstance(volume_id, str) or not SAFE_ID.fullmatch(volume_id):
        raise ValueError("Volume must have a stable UUID or PARTUUID")
    dest = Path(choice_path)
    dest.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".volume-choice-", dir=dest.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"volume_id": volume_id}, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, 0o640)
        os.replace(tmp, dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _selected(volumes, choice):
    # A saved choice must never fall back to a different USB disk.
    if choice:
        matches = [v for v in volumes if v["id"] == choice]
        return (matches[0], "selected") if len(matches) == 1 else (
            None, "selected_missing_or_duplicate")
    # Exactly one eligible volume: convenient automatic choice.
    eligible = [v for v in volumes if v["supported"] and not v["read_only"]]
    if len(volumes) == 1 and len(eligible) == 1:
        return eligible[0], "automatic_single"
    return None, "choose_volume" if volumes else "no_usb_volume"


def _mounted_path(vol):
    return next((p for p in vol["mountpoints"]
                 if os.path.ismount(p) and Path(p).is_dir()), None)


def _volume_info(v):
    """Copy user-facing metadata while keeping stored internal data immutable."""
    return dict(v, display_name=v["label"] or (v["disk"] or {}).get("model") or v["source"],
                selectable=bool(v["supported"] and not v["read_only"] and v["id"]),
                mounted=bool(_mounted_path(v)))


def inspect_usb(config_mount=None, *, lsblk_data=None, choice=None):
    """Return full USB inventory and the one selected recording destination."""
    if lsblk_data is None:
        lsblk_data, error = scan()
        if error:
            return {"detected": False, "mounted": False, "reason": "discovery_error",
                    "detail": error, "devices": [], "hardware": [],
                    "recording_root": None, "volumes": [], "selection_mode": "error"}
    else:
        error = None
    volumes, hardware = volume_inventory(lsblk_data)
    chosen_id = choice if choice is not None else selected_id()
    vol, mode = _selected(volumes, chosen_id)
    result = {
        "detected": bool(hardware), "mounted": False, "writable": False,
        "reason": mode, "selected_id": vol["id"] if vol else chosen_id,
        "selection_mode": mode, "devices": volumes, "hardware": hardware,
        "volumes": [_volume_info(v) for v in volumes],
        "recording_root": None,
    }
    if vol is None:
        return result
    result.update(source=vol["source"], label=vol["label"], filesystem=vol["filesystem"],
                  uuid=vol["uuid"], partuuid=vol["partuuid"])
    point = _mounted_path(vol)
    if point is None:
        result["reason"] = "selected_not_mounted"
        return result
    result.update(mounted=True, mount_path=point)
    try:
        st = os.statvfs(point)
        total = st.f_blocks * st.f_frsize
        used = max(0, total - st.f_bfree * st.f_frsize)
        free = st.f_bavail * st.f_frsize
        result.update(total_bytes=total, free_bytes=free, used_bytes=used,
                      used_percent=round(100 * used / total, 1) if total else None)
        # Pilot: don't treat root privileges as evidence that tspcam can write.
        folder = Path(point) / "TSP_Cam"
        if folder.is_dir() and not folder.is_symlink():
            target = folder
        else:
            target = Path(point)
        writable = (not vol["read_only"] and vol["supported"] and not (st.f_flag & os.ST_RDONLY)
                    and os.access(target, os.W_OK))
        result["writable"] = bool(writable)
        result["recording_root"] = str(target) if writable else None
        result["reason"] = None if writable else "selected_not_writable"
    except OSError as exc:
        result["reason"] = "storage_stat_error"
        result["detail"] = str(exc)[:180]
    return result


def _prepare_recording_folder(point):
    """Create only a new TSP_Cam folder on the verified selected USB.

    Never chmod/chown the filesystem root or an existing user directory.
    """
    root = Path(point)
    target = root / "TSP_Cam"
    if target.is_symlink():
        return "Recording directory is a symlink; refusing"
    if target.exists():
        return "Recording directory already exists"
    import pwd
    user = pwd.getpwnam("tspcam")
    try:
        target.mkdir(mode=0o750)
        os.chown(target, user.pw_uid, user.pw_gid)
        return "Created " + str(target)
    except OSError as exc:
        return "Could not create recording folder: " + str(exc)[:140]


def ensure_mount(*, choice_path=CHOICE_PATH):
    """Root mount service; never blindly mounts or alters arbitrary user disk."""
    if os.geteuid() != 0:
        return "root required"
    data, error = scan()
    if error:
        return "discovery_error: " + error
    volumes, _ = volume_inventory(data)
    vol, mode = _selected(volumes, selected_id(choice_path))
    if vol is None:
        return mode + "; not mounting anything"
    if not vol["supported"] or vol["read_only"]:
        return "Selected disk is not writable/mountable"
    existing = _mounted_path(vol)
    if existing:
        return "Already mounted " + vol["source"] + " at " + existing + "; " + _prepare_recording_folder(existing)
    # If it has another reported mountpoint, do not create a duplicate mount.
    if vol["mountpoints"]:
        return "Reported mounted elsewhere, awaiting mount availability"
    source = vol["source"]
    # Only kernel-generated block nodes, never user-given strings or arbitrary paths.
    if not re.fullmatch(r"/dev/(sd[a-z]+[0-9]*|nvme[0-9]+n[0-9]+p?[0-9]*)", source):
        return "Unexpected device path; refused"
    if not vol["id"]:
        return "No stable filesystem/partition identifier; refused automount"
    # Each device gets a stable independent mountpoint: no unmount-on-switch.
    digest = hashlib.sha256(vol["id"].encode("ascii")).hexdigest()[:16]
    root = MOUNT_ROOT
    target = root / ("usb-" + digest)
    if root.is_symlink() or target.is_symlink():
        return "Unsafe mount directory, refused"
    root.mkdir(mode=0o755, parents=True, exist_ok=True)
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        return "Mount directory is nonempty, refused"
    target.mkdir(mode=0o755, exist_ok=True)
    if os.path.ismount(target):
        return "Already mounted " + str(target)
    options = ["nosuid", "nodev", "noexec", "rw"]
    if vol["filesystem"] in {"vfat", "fat", "fat32", "exfat", "ntfs", "ntfs3", "fuseblk"}:
        import pwd
        user = pwd.getpwnam("tspcam")
        options.extend([f"uid={user.pw_uid}", f"gid={user.pw_gid}", "umask=0022"])
    # Confirm actual block node exists. No fallback to mounting a directory.
    if not Path(source).is_block_device():
        return "Block device disappeared before mount"
    try:
        call = subprocess.run(
            ["mount", "-o", ",".join(options), "--", source, str(target)],
            capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "mount_error: " + str(exc)[:160]
    if call.returncode:
        return "mount_error: " + call.stderr.strip()[:180]
    return "Mounted " + source + " at " + str(target) + "; " + _prepare_recording_folder(target)


def main():
    print("TSP_Cam storage: " + ensure_mount())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
