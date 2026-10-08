# TSP_Cam — MASTER IMPLEMENTATION PLAN
Status: planning baseline, 2026-10-08. No runtime has been deployed or tested yet.

## Mission
Replace MotionEye on TSP PiCam (Raspberry Pi Zero 2 W) with a robust, low-overhead, offline-first field recorder. The recorder and video evidence take precedence over all network, browser, update, and synchronization workloads. Keep the first version lean and test on real hardware before fleet adoption.

## Hardware and software baseline
- Primary hardware Pi Zero 2 W, 512 MB RAM, OV5647 5 MP (large installed inventory); CSI ribbon, separate microSD boot, USB recording drive, existing RTC and mains power for pilot.
- OS: **Bookworm Lite 32-bit and Trixie Lite 32-bit** must be compared on the actual Zero 2 W/OV5647 before choosing/pinning. Upstream Trixie + Zero 2 W memory issue #1358 requires qualification. Confirm libcamera/Picamera2/H.264 encoder availability; 64-bit can be benchmarked later.
- Python 3 via distro packages for Picamera2/libcamera; avoid conflicting pip-managed libcamera/Picamera2 packages. Lightweight stdlib/limited dependencies for control plane. systemd services.
- The camera library owns sensor/capture in **one process**. Preview cannot start a second camera owner.
- Actual profiles **discovered and validated**, not assumed: legacy 800x600, **1280x960@30 (4:3 full-FOV candidate)**, 1280x720@30, 1920x1080@30; do not advertise 720p60 unless a genuine matching sensor mode, actual capture fps and encoder pipeline are validated; OV5647 1296x972 is typically ~46fps, 1080p ~33fps.
- The OV5647 **1920x1080 sensor mode is centre-cropped**, while 1296x972 can preserve full sensor field of view. Do not select 1080p by default before comparing traffic coverage, quality, OCR and sustained FPS against legacy 800x600/1280x960.

## Component model (minimal processes)
1. **tspcam-capture**: single persistent camera owner: mode/camera discovery, H.264 hardware encoder, segmentation, burn-in overlay (if feasible), lores frames to preview subscribers only, monotonic record/liveness counters, safe stop.
2. **tspcam-control**: small authenticated HTTP server and static mobile UI; configuration validation, read-only storage browser, on-demand preview and status. Separate systemd unit, non-root.
3. **tspcam-agent**: background health, hardware/time/storage probes, durable event logging; may initially be bundled in a lightweight service. Reports independent of browser.
4. **tspcam-connectivity**: BlueZ/NetworkManager or documented equivalent for Android PAN and 15-min boot emergency Wi-Fi AP (AP password unique per Unit; auto-off timer; service restore; coexistence tested). No permanent SIM.
5. **tspcam-updater**: independently privileged, narrowly-scoped signed-release installer with transactional switch and rollback.
6. **tspcam-sync**: optional deferred uploader to TSP OS, consuming offline queue; Unit ID canonical in TSP OS.

Reduce daemon count if measurements show 512 MB RAM pressure; separation is logical, not an excuse for excessive Python process overhead.

## Configuration and identity
- One stable immutable device ID (UUID generated once) plus editable user-facing Box identifier and central TSP OS Unit link.
- Typed, schema-validated config in /etc/tspcam with atomic writes and backup; secrets in root-owned protected file.
- Dynamic capabilities expose supported controls only: exposure, AWB, frame rate, rotation, focus/zoom only if driver AND physical actuator support them.
- Record config version and provenance in audit log. Validate changes; apply to capture at controlled safe boundary with rollback. Never reset identity on normal software update.

## Video pipeline
- Start by proving plain hardware H.264 encode (no overlay/preview) at 1280x960@30 and 1080p30 to external USB for >48h. Record FOV, actual timestamps/FPS, USB integrity and 512MB RAM load.
- Build **in-frame overlay**: bottom right timestamp (OCR-recognizable), TSP logo and Box number, white on dark semi-transparent background. Overlay can render static elements once and update timestamp every second, but compositing may still cost per frame; benchmark on Pi Zero 2 W. Validate OCR across 800x600, 720p and 1080p with real AI; avoid moving stamp without OCR tests.
- Initial preview: low-res single still/JPEG 320x180 for 16:9, 320x240 for 4:3; on-demand 1/2/5fps capped, no unbounded queues, release camera requests promptly, drop stale frames, viewer timeout ~2min. Prioritize main encode and verify no capture loss. Test alternatives if MJPEG is too heavy on Zero 2 W.
- Logical recordings: 60min by default, configurable 15/30/60. Evaluate Picamera2 SplittableOutput with PyavOutput for I-frame-safe segment switches (no camera restart); explicitly test power loss recovery, finalized MP4, fragmented MP4/TS alternatives and frame timestamps. If resilience needs shorter physical segments, expose logical 60min grouping in UI and validate the TSP office workflow before changing physical file expectations. Never block capture during browse/download.
- Explicit missing USB policy (alert, retry) — no surprise write to boot SD. Mount by UUID and verify actual physical volume.

## Storage and technician file manager
- Detect exFAT, FAT32, NTFS, ext4 as reported by system; actual RW support tested. exFAT preferred for removable media used on Windows.
- Warn when FAT32 file size would exceed 4 GiB. UI may suggest exFAT. **No silent format**.
- Format tool is privileged isolated action: identify specific removable device (not system/root), require double confirmation with device name/capacity, refuse during active recording unless stopped safely, unmount, mkfs.exfat, verify, remount, report result, persist audit log OFF the formatted USB.
- Browser: only restricted recordings root, paginated date folders, filename search, file size and duration, on-demand small thumbnails, download selected file; disable arbitrary path traversal. Avoid full quality video stream over Bluetooth by default.
- Display remaining recording hours by profile based on actual filesystem free bytes, actual profile bitrate and safety headroom, calibrate from observed segment sizes. Clearly label estimate.

## Time, logs and health
- Boot system clock from verified RTC; synchronize using NTP through Android tether when available; update RTC and record time jumps. Derive overlay timestamp from capture metadata/monotonic-to-UTC mapping (not time of callback execution); log DST/timezone. Recording should report TIME INVALID when RTC implausible (define explicit start/block policy before production).
- Append compact, bounded crash-surviving events immediately on OS drive; rotate/export a consolidated per-day JSONL log to USB hourly and when reconnected. USB audit requires local surviving record.
- Check not just systemd status: actual frame/encoded-byte counter, file growing, USB mounted/write health, zero byte recordings, RTC, CPU temperature, RAM, undervoltage indicators, USB disconnects. Retry capture with bounded backoff.
- Recorder never waits for network, Bluetooth pairing, GitHub or TSP OS.

## Installer (one command)
- Fresh supported OS first (Raspberry Pi Imager), bootstrap via authenticated distribution; CURRENT repo is private, so unauthenticated raw GitHub install URL will not work.
- Installer prompts before privileged changes, checks architecture, camera, disk/mount, RTC, network; installs versioned release, configures systemd and web UI, validates actual sample recording, records installation report.
- No unattended destructive actions (OS image overwrite, USB format, identity reset).
- Prefer signed release artifacts with verified pinned public signing key, not direct curl|sudo bash from moving main.

## OTA updater
- Read-only checking and release-note display; explicit human confirmation for install.
- Trusted signed release manifest, sha256 artifact, compatibility gate, private read-only release access via short-lived TSP OS proxy or pilot scoped token.
- Download to SD staging while recording. Before activation, acquire update lock, ensure enough disk/power, close a segment cleanly, swap atomic current symlink, restart and verify real recording, then commit; boot-time reconciliation + rollback to last good on failure.
- Preserve config/identity/SQLite metadata and all USB recordings. Application rollback is NOT an OS/kernel rollback. Safely migrate schemas / backup first.
- API is never root; privileged updater has restricted entry points; no arbitrary command input from browser.

## Acceptance gates
**Gate A: baseline:** clean OS, sensor auto-detect, accurate RTC, stable identity/config.
**Gate B: capture:** 24-48h 720p30 and 1080p30; real readable segments, target FPS, timestamp OCR pass, USB free space and correct FOV, low RAM, no unexpected gaps. Test at least one real power loss (acknowledge active segment risk).
**Gate C: control:** background recording + user file search, live 2fps preview, format dry-run; CPU/thermal/RAM and recording gap comparisons.
**Gate D: connectivity:** one Android phone Bluetooth pairing/PAN, temporary Internet, service panel IP, boot emergency AP reachable for 15min and then off; recovery after radio/phone disconnect.
**Gate E: OTA:** valid signed release, bad signature rejection, loss of Internet mid-download, failed service startup, interrupted activation/reboot, rollback including SQLite compatibility.
**Gate F: pilot:** at least 3 PiCams / drives with varied wear, 48-72h installs, field staff feedback, then canary rollout before fleet.

## Sequenced execution tasks
P0: reproducible OS setup, repo Python package + tests, systemd, diagnostics, sample modes.
P1: capture CLI (bare H.264/USB/segments/RTC/counters) and B acceptance.
P2: overlay and low FPS preview with load test and OCR.
P3: storage manager, safe format flow, file browser, duration estimator and web UI.
P4: Bluetooth PAN, Wi-Fi emergency fallback, authenticated technician access.
P5: transactional signed release OTA, installer and rollback tests.
P6: TSP OS sync, Unit records and rollout tooling.
Battery telemetry / timed power / optional autofocus and optical zoom are modular future work, not pilot blockers.

## Unresolved items / measured decisions
- Which actual RTC chip, USB adapter/drive models, and boot SD capacity; probe on unit.
- OV5647 sensor/encoder profile and real FOV, particularly legacy 800x600.
- Which container/segment strategy gives both crash safety and Windows office compatibility.
- Overlay implementation cost at 1080p30; if expensive, compare GPU/compositor options or simpler burned-in glyphs.
- Reliability of Android PAN across technicians' phone models, and whether Wi-Fi AP simultaneous Bluetooth is stable.
- Safe recovery physical trigger for extending AP window if Bluetooth fails.
- Update integrity/signing service and read-only release delivery architecture for private repo.
- Objective acceptance metrics (max gap, frame loss, current draw) set after baseline hardware test.

## Critical review

Before implementation, review [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md). It documents concrete upstream issues, the 1280x960 full-FOV candidate, OS qualification, preview buffer safety, non-journaled exFAT, file segmentation, AP recovery and acceptance tests. Risk findings override premature default selections above.

## Technology reference

See [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) for the researched production candidate: distro libcamera/V4L2 H.264, Picamera2 and PyavOutput/SplittableOutput, NetworkManager/BlueZ, bounded systemd monitoring, and rejected alternatives. These remain benchmark candidates until proven on a real OV5647 Zero 2 W.

## Binding field operation requirements (2026-10-08)

[FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) overrides earlier exploratory alternatives on these matters:
- Begin recording automatically **on boot once usable USB is mounted**, or on later USB insertion; never depend on phone/panel.
- Preserve **physical hourly MP4 files** compatible with the TSP office's repair workflow; do not deploy shorter physical clips or a different container without explicit agreement and field compatibility tests. The exact 60-min rotation alignment is awaiting confirmation.
- **No overwrites, no circular deletion.** On USB full -> alarm and stop. Use unique collision-resistant filenames even after RTC changes and reboot.
- Timestamp AUTO versus MANUAL mode is persisted. MANUAL must not be overwritten by background NTP; explicit set time updates system clock and hardware RTC. AUTO can use internet NTP over Android PAN and save to RTC, phone time comparison in authenticated panel only warns unless user confirms correction.
- Technician checks low-FPS view, active filename and real recording progress, as well as RTC status/clock mismatch.
- **Power Down powers off the complete Pi**, after recording close and buffered writes are flushed; do not imply it cuts external battery power.
