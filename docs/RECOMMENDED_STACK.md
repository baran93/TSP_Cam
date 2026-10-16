# TSP_Cam — researched software stack and reliability decisions (2026-10-08)

Status: **design decision + validation requirements; not implemented or benchmarked**. This complements [MASTER_PLAN.md](MASTER_PLAN.md) and [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md).

## Selected stack

| Layer | Pick | Rationale |
|---|---|---|
| OS | Raspberry Pi OS Lite **32-bit**; **Trixie vs Bookworm A/B test** before production | 512MB RAM, distro-matched camera dependencies. Upstream report #1358 describes Trixie malloc mode-query failure on Zero 2 W with IMX477 (NOT OV5647), so don't assume all setups fail. |
| CSI camera | Kernel `ov5647`, V4L2/media-controller, libcamera Raspberry Pi pipeline | Supported modern driver stack, no legacy MMAL/OMX. |
| Primary recorder | Python `Picamera2` + `H264Encoder` (V4L2 hardware codec) | Single sensor owner, access to camera mode, overlays, main+lores capture, sensor metadata. |
| File writer | `SplittableOutput(PyavOutput(...))` (version-tested) | Official example splits MP4 at I frame without stopping capture. Test timestamp behavior and unclean power failure. |
| Diagnostic recorder | `rpicam-vid -n -t 0 --inline ...` | Vendor maintained, fewer moving parts. **Do not automatically switch to stamp-less footage in production** without an accepted OCR-compatible fallback. Only one process may own the CSI camera at a time. |
| Overlay | Picamera2 `MappedArray` / `pre_callback`; pre-render logo/label/timestamp glyphs, composite small ROI | Stamp must be burned into encoded image for current TSP AI; per-frame compositing still incurs CPU cost. |
| Low-FPS preview | Shared Picamera2 lores YUV stream; lightweight JPEG snapshot on demand; throttle to 1–2 FPS, no continual encoder | Never re-open sensor; do not retain capture requests or an unbounded frame queue; lower preview priority than main. |
| Local API / GUI | Tiny authenticated Python HTTP app + static HTML/CSS/JS | Avoid GUI desktop, Electron, large services; defer selection of framework until RAM benchmarking (stdlib HTTP or lightweight aiohttp/Flask). |
| Device manager | `systemd` services + independent health verifier | restart on crash; watchdog only when real frame/output progress; bounded backoff and gap/audit log. |
| Network | BlueZ + NetworkManager; Android PANU client, NetworkManager Wi-Fi AP | Existing supported implementations; test real Android PAN and reconnect; emergency AP first 15min + physical recovery path. |
| Clock | Linux I2C RTC driver (`rtc-ds3231` etc only after chip detection) + systemd timesync/chrony as validated | RTC source of truth offline; NTP correction when internet available; robust timestamp mapping/logging. |
| USB filesystems | Linux kernel drivers, exFAT preferred for Windows interchange, ext4 alternative for resilience | exFAT lacks metadata journal; **do not assume support means durable under sudden removal**. |
| State and sync | Bounded SQLite events on persistent SD state + hourly JSONL export to USB | No network dependency; survive USB format; SQLite must not be stored under tmpfs overlay. |
| OTA | Signed release tarball, atomic switch, service health, rollback | Application updates only; no unmanaged `apt full-upgrade` during field recording. |

## Why not the alternatives
- **No MMAL/OpenMAX `h264_omx`**: legacy API and dependency from current MotionEye.
- **No FFmpeg `libx264` for always-on encode**: CPU rather than Zero 2 W hardware. If FFmpeg is needed, remux with `-c:v copy` not decode/re-encode.
- **Avoid `FfmpegOutput` by default**: Raspberry Pi Picamera2 examples explicitly say it is no longer the recommended MP4 writer; use PyavOutput.
- **GStreamer**: technically valid, but complex plugins/caps/buffering create extra failure surface without clear MVP benefit. Reassess only if Picamera2 benchmarks cannot handle preview or required muxer.
- **Do not spawn multiple camera processes or second H.264 encoder** for low-FPS preview. Shared lowres YUV and very occasional JPEG snapshots.
- **Do not require Docker** on Zero 2 W field cameras; systemd and OS packages are sufficient.
- **Do not introduce a separate motion analysis / object detection pipeline** on the device.

## Specific critical compatibility facts
1. OV5647 kernel modes include **1296x972 at ~46 FPS with binned full field-of-view**, and **1920x1080 at ~33 FPS centre-cropped**. 1280x960@30 is a strong 4:3 candidate; inspect actual sensor selection. **720p60 not supported as an assumption**: digital upscale/downscale does not create new sensor samples; offer FPS only if available and verified.
2. Pi Zero 2 W official capability: hardware H.264 encode up to 1080p30 and USB 2.0 OTG; real 1080p30 plus overlay/preview needs benchmarking.
3. Initial encoder bitrate preset **not lower than safe test results**; default 5 Mb/s for 1080p30 is *only an initial benchmark candidate*, and some high-motion patterns can stall too-low bitrates. Include dynamic complexity test and inspect encode progress. Consider 8–10Mb/s if needed for traffic details and robustness.
4. Ordinary unfinalized MP4 is at risk if power is cut before close; production files are physical MP4 segments at full wall-clock hours with a shorter first file (D8). Shorter physical segments with logical hourly grouping were only an exploratory recovery idea and are not approved. Test crash recoverability and compatibility with the TSP MP4-repair workflow. Fragmented MP4 / MPEG-TS remain laboratory comparisons only, not an automatic switch.
5. `Picamera2` package should be installed via apt (`python3-picamera2 --no-install-recommends`) to keep libcamera versions compatible; do not blindly mix pip and distro bindings.
6. Overlay glyph cache can update only once a second, but must still be composited into each output frame; cannot assume free CPU processing.
7. Recording and preview sharing a camera stream is the default design; a browser frame must be copied/released immediately and never held back for a slow Bluetooth connection.
8. Monitor timestamps from capture metadata and output frames to spot silent stalls; systemd service-alive alone is not enough.
9. NetworkManager can create AP with `nmcli device wifi hotspot`; it supports Bluetooth PAN client profiles (`bluetooth.type panu`), but real Android version/device behavior may vary.
10. RTC device type and boot image are **not** yet measured: detect first and avoid blindly installing module overlays for unconfirmed chips.

## Engineer-mode bring-up checklist (read-only commands for the first test unit)
```bash
cat /etc/os-release
uname -a
cat /proc/device-tree/model
rpicam-hello --list-cameras
lsblk -o NAME,MODEL,TRAN,FSTYPE,SIZE,LABEL,UUID,MOUNTPOINTS
vcgencmd get_throttled
free -h
systemctl --no-pager --failed
```
All are diagnostic and should not erase or alter recordings.

## Benchmark matrix (baseline then extra capabilities)
1. A/B test a freshly imaged **Bookworm Lite 32** and **Trixie Lite 32** using identical OV5647, USB and power. Record kernel/libcamera/Picamera2 versions, free RAM, capture success, CPU and temperature.
2. Capture 1280x960@30 and 1920x1080@30 bare H264 + timestamps: compare real FOV from fixed tripod and sustained frame timing for 24–48 hours.
3. Add PyavOutput and I-frame switching as close as feasible to full wall-clock hours (including a short first file); playback all segments with ffprobe and target office tools; assess shutdown/power-loss behavior, DST and time corrections.
4. Add timestamp/logo burn-in and measure CPU/stall/dropped frames. Test TSP OCR accuracy.
5. Add lowres preview 1/2 FPS; open/close 100 times, induce slow readers and Bluetooth packet delay; verify main capture is unaffected.
6. Simulate missing mountpoint, read-only/full USB, accidental USB unplug and sudden power-off (repeat), confirm device ID audit/gap logs survive where possible.
7. Only then decide OS/bitrate/container/profile production defaults and lock release image/versions.

## Sources (official first)
- https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/
- https://www.raspberrypi.com/documentation/computers/camera_software.html
- https://github.com/raspberrypi/picamera2 (apt installation recommendation)
- https://github.com/raspberrypi/picamera2/blob/main/examples/split_output.py
- https://github.com/raspberrypi/picamera2/blob/main/examples/mp4_capture.py
- https://github.com/raspberrypi/picamera2/blob/main/examples/timestamped_video.py
- https://github.com/raspberrypi/picamera2/issues/1228
- https://github.com/raspberrypi/picamera2/issues/1085
- https://github.com/raspberrypi/picamera2/issues/1358
- https://lists.libcamera.org/pipermail/libcamera-devel/2020-June/009766.html
- https://www.networkmanager.dev/docs/api/1.34/nmcli-examples.html
- https://learn.microsoft.com/en-us/windows/win32/fileio/filesystem-functionality-comparison
- https://pip.raspberrypi.com/categories/685-whitepapers-app-notes-compliance-guides/documents/RP-003610-WP/Making-a-more-resilient-file-system.pdf
