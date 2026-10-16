# Phase 0 pilot: one-command installation and read-only LAN panel

**Status:** PR #3 on actual pilot Raspberry Pi. Responsive read-only LAN dashboard and prototype on-demand camera preview, **not** a field recorder or signed OTA.

## One command with temporarily public repository

Only while the owner makes this repository public, and after reviewing the branch:

```sh
d=$(mktemp -d) && curl -fsSL https://api.github.com/repos/baran93/TSP_Cam/tarball/chatgpt/phase0-python-installer | tar -xz --strip-components=1 -C "$d" && sudo bash "$d/scripts/install-local.sh" && tspcam status
```

Does not require Git or a GitHub SSH key. If the repository is private again, unauthenticated downloads fail. Code/history may be copied while public. This shortcut is **only for trusted pilots**; production plans need signed release artifacts.

Requires Raspberry Pi OS Lite, Python 3.11+, systemd, curl and tar. The installer also installs Raspberry Pi OS apt packages `python3-picamera2` and `python3-pil` if Picamera2 is not already importable; camera support depends on installed OS/libcamera drivers. From an already downloaded, trusted checkout, run `sudo bash scripts/install-local.sh`.

## Access from a PC or phone on the same LAN

The pilot read-only dashboard listens on all Pi interfaces (`0.0.0.0:8765`); open `http://<PI_IP>:8765/` from a PC or phone on the same reachable network. Discover IP via `hostname -I` or `ip -4 addr`. Ensure the access point does not enable client isolation.

**Pilot risk:** no authentication or TLS. Anyone with network access can read device status (hostname, USB state, etc.). Do not enable router port forwarding or publicly expose port 8765; this is not production behaviour.

## Camera preview prototype

Open dashboard on `http://<PI_IP>:8765/` and the Live View page requests `/api/preview.jpg` at 1 fps. First frames may show a placeholder while Picamera2 starts; the status panel shows the real camera error if it fails. When the page is no longer requesting frames, the camera is stopped/released after about 15 seconds. No JPEGs are written to the SD or USB. Snapshot downloads the latest fresh JPEG only. The preview is currently the only process owning the camera; once the H264 recorder exists, preview must be integrated with the recorder capture pipeline.

It is a PIL/Picamera2 proof-of-concept on OV5647. Real hardware testing and FPS/power validation remain outstanding.

## Verify

```sh
tspcam status
systemctl status tspcam-agent tspcam-web --no-pager
curl -fsS http://127.0.0.1:8765/api/status
ss -ltn | grep ':8765'
```

On disk:
- `/opt/tspcam/releases/pilot-<hash>/` immutable-ish snapshot (release directory mode `0755` so nonroot can traverse).
- `/opt/tspcam/current` atomic symlink to current release; `previous` to prior release.
- `/etc/tspcam/config.toml` preserved between installs. Pilot permissions: directory 0755, file 0644 for non-root CLI. Store **no credentials** in pilot config; move secret values to separate protected storage in future.
- `/var/lib/tspcam` holds persistent state; no USB footage.
- `/usr/local/bin/tspcam` is CLI entrypoint.
- `tspcam-agent.service` and `tspcam-web.service` are diagnostics/status only.

### Resolved pilot issue

The initial script created staging with `mktemp -d` (mode 0700) and moved that directory unchanged into releases; ordinary `pi` user and `tspcam` service therefore could not traverse `/opt/tspcam/current`. Corrected to set release directory mode 0755; also fixed a malformed temporary symlink path in an intervening commit.

This installer does **not** implement H.264/MP4 recording, Bluetooth PAN, Wi-Fi AP, RTC updates, authentication or fleet OTA. It **does** implement experimental live JPEG preview and persistent camera-profile settings; the recording resolution is only a future intent until the real recorder is written.

## USB storage pilot

A physically attached USB filesystem is discovered using `lsblk` (only USB transport, not SD). The installer enables a conservative `tspcam-usb-mount.timer` that checks every 30 seconds for a single eligible USB filesystem, and the one-shot mount service attempts to mount it to `/media/tspcam`, without formatting. Existing valid USB mounts such as `/media/usb0` are reused instead. More than one ambiguous unmounted USB volume is not auto-selected.

The dashboard distinguishes **USB detected**, **mounted**, and **writable / future recording destination**. If the volume is unmounted, read-only, inaccessible to the web service or not a supported format, it cannot be a recording destination. **Never fallback to the microSD**. This does not start any MP4 recording.

Check after installation:

```sh
lsblk -o NAME,TRAN,TYPE,FSTYPE,MOUNTPOINTS,LABEL,SIZE
systemctl status tspcam-usb-mount.timer tspcam-usb-mount.service --no-pager
tspcam status
```

## Preview and device settings

The technician panel has PNG branding based on the owner's image. Choose live preview resolutions `640x480`, `800x600`, or `1280x720`, and `1`, `3`, or `5` FPS. Frames are JPEGs in RAM; live preview releases the camera after inactivity and resumes on next request. The actual FPS and power consumption require validation on the owner's Zero 2 W; 5 FPS is an upper requested rate, not a measured guarantee. Settings are stored in `/var/lib/tspcam/settings.json`.

The recording resolution dropdown is persistent but has no effect until the recorder component is implemented. These are safe setup experiments only.
