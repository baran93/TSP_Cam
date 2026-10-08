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
