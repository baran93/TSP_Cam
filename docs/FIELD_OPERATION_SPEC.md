# TSP_Cam — Field Operation Contract

Date: 2026-10-08. Status: **user-confirmed operational requirements**; technical implementation and power-cut recovery require validation on real Raspberry Pi.

This document has priority over older proposals whenever they differ in operational behavior. See [MASTER_PLAN.md](MASTER_PLAN.md), [FIELD_REQUIREMENTS.md](FIELD_REQUIREMENTS.md), [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md).

## Mission

A technician brings up a PiCam, positions it using a low-FPS preview, confirms camera time and recording-file existence/progress, and leaves. Routine setup should never require manually starting recording or changing settings. The camera operates fully offline with RTC and USB.

## Recording and media invariants

1. **Autostart**: on every Pi boot, after camera/RTC and actual recording drive mount have been checked, start continuous recording immediately if eligible USB media is present and writable. Do **not** wait for technician Bluetooth, internet, login, web UI, update check or preview.
2. If USB is absent, not actually mounted, read-only, out of space or fails write-health checks, indicate WAITING_FOR_USB / RECORDING_ERROR; continue monitoring for a viable USB device and autostart on insertion without reboot. Never silently write to system microSD through an empty mountpoint.
3. **Never overwrite any existing video** and never delete videos to free space. No circular/loop recording or silent cleanup. Use O_EXCL/unique atomically reserved paths, robust collision handling and a stable run/session ID as needed. Preserve files even when clock steps backwards or two restarts occur in same second. If storage fills, stop capture and signal an alarm.
4. Physical video files are intended to be **one-hour files** as in the existing TSP MotionEye workflow. Default: 3600 seconds segment duration. **Confirmed: rotate after 3600 seconds of elapsed capture time from the recording start, not at the top of the wall-clock hour.** A segment may end on the next suitable H.264 keyframe to preserve continuity; measure interval with a monotonic clock. Do not change the established filename pattern or split into shorter physical clips without explicit consent.
5. Use a Windows/TSP-office-compatible MP4 output only after testing. On abrupt cutoff, an active MP4 may be unfinalized; office technicians currently use “MP4 Fix” to repair it. Preserve damaged originals and do **not** automatically delete or rename broken segments as if fixed. Prior closed segments must remain readable.
6. File naming carries date/time at creation (equivalent to existing `%Y-%m-%d-%H-%M-%S` format), under per-unit/per-date folders. Ensure uniqueness even when RTC is manually moved backwards, corrected or unavailable.
7. On active capture, the system must prove more than file presence: monitor actual encoded frame progression, file size/bytes changing (recognize buffering), recent write errors, mount identity and time of last successful segment close. Present active filename + `Recording / File created / Writing / Time` status. Files being written do not need to be viewable until finalized.
8. Failed USB/unplug must not cause a new file to be silently created on the root microSD. Reinserted USB should resume capture into a new unique file, preserving partial evidence.

## Timekeeping — user-selectable policy

Persist explicit mode:
- **AUTO (initial default):** on boot restore system time from RTC and begin recording promptly; when internet becomes available via Android Bluetooth tethering, NTP can correct system time and update hardware RTC. If the technician opens the authenticated web panel, the phone browser can provide a current device timestamp through `Date.now()` to compare with camera time, without silently overwriting the clock. Use NTP as preferred authoritative source where reachable; phone clock may be inaccurate.
- **MANUAL:** allow technician to enter date, time (with explicit timezone) and choose `Set camera time`; update both system clock and RTC and persist MANUAL mode. Disable background NTP/automatic synchronization while manual mode is active, otherwise Linux can overwrite the requested time. No implicit RTC rewrite from phone or Internet until operator switches mode to AUTO or clicks an explicit update.
- **Update time** action (only with user consent): select source Phone or Internet/NTP where available; show source, phone-camera offset and whether RTC is responding; update both software time and RTC, audit technician/source/old/new values; if large time jump, rotate safely or mark time discontinuity, prevent filename collisions and warn that timestamp in current video may jump.
- **RTC fault:** show plain-language `No communication with RTC module`, do not pretend time is valid; record this failure persistently. Boot policy for invalid time must be deliberate: recording can continue to preserve evidence but must show warning and time validity in logs. Do not stop capture just because phone is absent.
- The panel compares phone-provided epoch milliseconds with camera wall-clock at authenticated request and reports estimated difference, including a tolerance to allow network/request latency. It is only a helpful technician indicator, not proof that phone UTC is accurate. Display timezone explicitly. Never mistake phone timezone differences for a clock offset. Browser cannot guarantee a direct NTP/RTC reading without API support.
- Clock corrections and reboot events must be logged and clearly reflected in camera metadata, recording names and filenames, without overwriting existing evidence.

## Technician panel — installation view

Priority top screen:
- Low FPS shared video preview (1–2fps initially; on demand, timed out; never blocks capture).
- Box ID, detected camera module, resolution, recording state.
- USB mount/health/free space, estimated remaining hours.
- **Current active filename**, file created status, recent encoder progress/bytes, start timestamp; do not require playback of open MP4.
- **Camera time** displayed with source AUTO / MANUAL / RTC INVALID.
- **Phone time** displayed, discrepancy warning if outside configurable tolerance.
- Simple explicit **Update Time** and **Set Manually** controls, gated appropriately.
- RTC detection error (e.g. `RTC not responding`); simple troubleshooting details on request.
- One clear **Power Down** button.

Minimal technician flow:
1. Connect power + USB, recording auto-starts once usable.
2. Connect Android Bluetooth PAN (or fallback 15-minute Wi-Fi AP), open panel.
3. Aim camera using low FPS preview.
4. Verify recording status, current filename created and data is progressing.
5. Verify camera date/time matches expected survey schedule or intentional manual time.
6. Leave recording alone, or use Power Down for safe removal.

## Safe Power Down

`Power Down` is **full Raspberry Pi OS shutdown**, not merely “stop recording”.
- An authenticated action with confirmation prevents accidents.
- Request capture to finish/close current MP4 segment, flush data and filesystem buffers, persist pending audit logs, synchronize USB when relevant, and unmount/eject USB if safely possible.
- Initiate `systemctl poweroff` (with carefully scoped privilege), let systemd service stop ordering handle cleanup.
- Show a shutdown-in-progress page and a simple instruction to **wait until the Pi has actually halted / storage activity has stopped** before unplugging power or removing USB.
- If capture close, sync or unmount fails/timeouts, report critical error before progressing where possible, and avoid claiming “safe” without proof. A dead camera process may require bounded forced recovery; no guarantee against simultaneous physical power removal.
- Pi shutdown does **not necessarily electrically disconnect** an external powerbank; future hardware cutoff is separate.
- Log reason, timestamp and outcome in on-device durable state before powering down; copy to USB later if available.

## Media formatting and technician mistakes
- Formatting is always a separate service action, **never part of boot or routine install workflow**.
- Double confirmation + clearly identified removable device; no system/root SD formatting. Save format audit OFF target USB.
- On FAT32 report 4GiB file limit and offer exFAT after technician approval, but never force formatting.
- No automatic delete or overwrite under low storage conditions.

## Logging
- Record important events immediately to a bounded persistent local journal (where the chosen OS permits durability); export to USB in a single per-day log file hourly.
- Include boot, clock mode/time source/adjustments/RTC failure, active file creation/progress, USB mount identity, recording gaps, format action, shutdown and failed writes.

## Acceptance tests added
- USB inserted before boot -> first recording starts with no interaction, independent of phone/web UI.
- USB inserted after boot -> recording auto-starts without reboot, no writes to underlying OS mountpoint.
- Full USB -> stops, warns, never deletes/overwrites.
- Reboot + same timestamp/clock moved backward -> unique video filename, old file bytes unchanged.
- Hourly physical MP4 split at 3600 seconds elapsed from capture start (not top of hour); repairs by actual office `MP4 Fix` on damaged file, playback by existing TSP AI/Windows process.
- AUTO with no phone: RTC startup recording; when PAN/internet returns NTP updates RTC and logs time change.
- MANUAL persists reboot and resists NTP overwrite. Explicit Update time modifies RTC with logged source.
- RTC absent/broken displays an honest fault and does not silently show a fake synchronized state.
- Phone time mismatch warns but does not auto-correct in MANUAL mode.
- Power Down closes active segment, flushes, powers off entire Pi; technician waits for hardware halt.
- Video progress reporting checks real frame/encoder and bytes, not file existence alone.

## Remaining user decision
**Resolved 2026-10-08:** 3600 seconds elapsed from recording start; no wall-clock hour alignment. Start at 14:17 -> rotate at approximately 15:17 (next keyframe), then approximately 16:17. A reboot or safe shutdown starts a new session/short final file as needed. Wall-clock corrections must not change the interval or cause filename collisions.
