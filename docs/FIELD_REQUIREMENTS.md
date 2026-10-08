# Field camera requirements — 2026-10-08

Status: initial product assumptions; hardware validation required.

## Hardware
- Raspberry Pi Zero 2 W with OV5647 5MP sensor.
- Continuous capture; **no motion detection**.
- Test profiles: 800x600@25/30, 1280x720@25/30, 1920x1080@25/30. Optionally test 720p60.
- Target default: 1080p30 if 24-hour reliability, image quality and battery-life testing pass; otherwise 720p30.
- Prefer hardware H.264 through rpicam/libcamera. Preview disabled except on demand.
- 60-minute logical recording files by default; offer 15 and 30 minutes.
- Prefer MP4 deliverables, but verify crash safety and segment integrity; raw H.264 + remux without re-encoding is an option. Use --inline with rpicam-vid --segment if that backend is selected.

## Storage
- Default: mounted USB drive. Optional destination: microSD selected from local panel.
- Validate mountpoint/device identity, free space and write permission before recording.
- Never silently fall back to the SD card when USB disappears; alert and apply explicit configured failure policy.
- USB format compatibility, permissions, write durability, unexpected power failure and storage exhaustion need field tests.
- Avoid heavy writes to system microSD.

## Logs
- Local operational events recorded immediately (small persistent queue or journal); not just once per hour.
- Export/refresh one consolidated log file on USB at least hourly, alongside footage (prefer daily rotating JSONL file; avoid an unbounded single fleet-lifetime file).
- Logs include boot/shutdown, capture start/stop, camera faults, storage capacity, RTC status, reconnect, configuration changes, sync state, restart reasons.
- On USB failure, retain a bounded local emergency log and later copy it to USB.
- Use UTC machine-readable timestamps and preserve local/field time for display. Track clock corrections.

## Connectivity
- Bluetooth primary for setup, diagnostics and temporary Internet via technician's phone; validate PAN/tethering behavior by Android/iPhone version.
- Emergency Wi-Fi access point automatically active during first **15 minutes after every boot**, with unique SSID and strong unique password.
- AP auto-off after 15 minutes, extendable from authenticated panel and re-openable through a documented physical service/recovery method.
- Wi-Fi and Bluetooth can coexist but need field testing for radio/power interference on Zero 2 W.
- Wi-Fi AP should be access-restricted; no default shared fleet-wide password.
- Networking and panel crashes may **never** stop local recording.

## Technician UX
- Mobile-first minimal screen: camera ID, RECORDING/ERROR state, recent segment, USB presence/space, RTC/time, temperature, Internet/Bluetooth.
- Configurable resolution, FPS, bitrate preset, segment length and target storage.
- Preview on demand, with explicit timeout to reduce CPU/power.
- Safe reboot/shutdown and service controls with confirmation.
- Large plain-language alerts: NO USB, CAMERA ERROR, NOT RECORDING, RTC ERROR.
- A configuration change must be validated and applied at safe segment boundaries where feasible, with rollback on failure.
- Tie each PiCam identity to central TSP OS Unit (single source of truth).

## Acceptance criteria
1. 24-hour unattended recording test at 720p30 and 1080p30; count gaps/dropped frames.
2. Measure CPU, temperature, power draw and battery runtime on Zero 2 W.
3. Boot Wi-Fi AP, pair/connect Bluetooth, test phone tethering, verify Wi-Fi auto-off at 15 minutes.
4. Physically remove USB, kill capture process, disconnect phone and cut power; verify recovery behavior and readable previous segments.
5. Export hourly USB logs and replay offline events once connectivity returns.

## Storage duration estimator (technician panel)
- Read actual available free space using filesystem statistics (`statvfs` / `df`) on the configured mounted recording volume, not the nominal USB size.
- Display estimated available recording hours beside every offered recording profile (800x600, 720p, 1080p) and refresh when USB or profile/settings change.
- Use the bitrate associated with each profile, **not resolution alone**; H.264 file size depends on bitrate, FPS, scene motion and encoder settings.
- Formula: `hours = available_bytes * 8 / (bitrate_bits_per_sec * 3600)`, adjusted for container overhead and a configurable storage safety reserve.
- Label values as **estimates**, not guarantees. Prefer calibration using observed recent segment sizes and use the lower (more conservative) prediction when actual bitrate differs from nominal.
- If USB is missing, unmounted, read-only or full, show a prominent warning instead of a misleading hours estimate.
- Display remaining hours for the selected storage target, and allow comparing profile estimates without changing active recording.
- In the UI also show available disk space in GiB and the current active profile.

## File browser and playback
- Local technician panel must allow selecting a configured recording drive (default USB), browsing folders, sorting and searching filenames, filtering by date/time, and showing file size/duration where known.
- Offer metadata and thumbnails on demand; preview and download existing clips without interfering with active recording.
- Bluetooth transfer/playback of full bitrate videos is not guaranteed; use low-bandwidth thumbnails or short preview clips and optional local download. Never scan entire USB on each page load; use paginated browsing.
- Prevent path traversal and limit reads to configured approved recording roots.

## Compatibility stamp / OCR requirement
- Existing MotionEye overlay format is an AI integration contract, not a cosmetic preference.
- Reference frame supplied 2026-10-08: lower-left two-line date/time; lower-right TSP/site/camera identifier; white block/pixel-like glyphs with dark outline.
- Preserve field text, typography, shadow/outline, margins and exact reference pixel coordinates **at 800x600**; verify with original full-resolution reference sample and OCR regression tests.
- Provide matching scaled stamp geometry for 720p and 1080p, but verify OCR empirically rather than assuming scaling is compatible.
- Candidate: Raspberry Pi's official Picamera2 `examples/timestamped_video.py` using `MappedArray` + `pre_callback` before H.264 encode; optimize via cached/pre-rendered glyph overlay to avoid full-frame transformations.
- Avoid FFmpeg decode/drawtext/re-encode of all frames on Zero 2 W; expensive and may not sustain 1080p30.
- Record UTC acquisition time in metadata and render the desired local date/time in the in-frame stamp; validate RTC corrections during capture.
- Acceptance: compare MotionEye / TSP_Cam frames at 800x600 and run TSP AI OCR tests across timestamps, varying lighting and resolutions. Test sustained FPS with overlay enabled.

## Direct USB write performance
- Zero 2 W USB 2.0 OTG should have ample bandwidth for 3–10 Mb/s H.264 (~0.375–1.25 MB/s), but sustained performance is conditional on actual drive, OTG adapter, mount configuration and stable power.
- Capture directly to mounted USB; do not stage full clips onto the SD card.
- Validate real USB device identity, sustained sequential write performance, storage reliability and behavior on surprise power loss.
- Separate high-priority recording writes from any panel preview, download or health scanning.
- Verify read/write contention while technician browses existing recordings during capture.

## 2026-10-08 hardware / operating system decisions
- Initial OS candidate: Raspberry Pi OS Lite 32-bit Trixie on Pi Zero 2 W. Benchmark vs Lite 64-bit and freeze OS/kernel/camera dependency versions only after successful field validation.
- Test initially with mains supply and USB; batteries later. Technician phone platform: Android.
- Current fleet sensor: OV5647 (approximately 400 modules owned). Detect sensor model and advertised video modes dynamically through libcamera/rpicam.
- Use capability-driven camera settings. Hide autofocus, manual motor focus, optical zoom, etc unless the sensor/actuator and its driver expose real compatible controls.
- Future replacement camera modules must not require rewriting the recorder/UI.
- Preview must share the same camera capture pipeline as the recorder (main + lores). Start at ~2 FPS, lores 320x180 for 16:9 / 320x240 for 4:3; stop preview automatically on inactivity. Benchmark hardware encoding plus stamp plus preview for missed frames.
- Prefer exFAT for removable recording USB because Windows computers need to access recordings. Detect ext4, FAT32, exFAT, NTFS and report actual supported read/write capability, not blanket compatibility promises.
- Provide a guarded Format USB action: exact removable device identity/capacity shown, double confirmation, prohibit boot/root device, stop recording and unmount safely, format to exFAT, validate and remount, log operator action and result.
- Store format audit event persistently **off the formatted USB**, and export a copy to USB/TSP OS later. Never assume an hourly USB log alone can preserve a record of USB formatting.
- On FAT32 alert about 4 GiB per-file limit, optionally suggest exFAT without auto-formatting.
- Capture and persistent event recording must survive disconnects and power glitches where technically possible.

## Further engineering validation
- Prototype physical unit diagnostics: power undervoltage, USB disconnect/reconnect, real mountpoint verification, RTC validity, thermal and disk write errors.
- Verify actual FOV/crop for OV5647 at every proposed mode; high resolution must not sacrifice junction coverage.
- Test whether the encoder/overlaid timestamp can hold 1080p30 for 24–48h while USB is being browsed and low-fps preview is active.
- Define a stable unit identifier distinct from current friendly box label; ensure configuration is backed up for reflashing.
- For BT PAN on Android, test the concrete phone and OS version before treating the connection method as universal.
