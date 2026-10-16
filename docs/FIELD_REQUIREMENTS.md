# Field camera requirements — 2026-10-08

Status: initial product assumptions; hardware validation required. Aligned with [DECISIONS.md](DECISIONS.md) on 2026-10-16; decisions take precedence ([AGENTS.md](../AGENTS.md) §4).

## Hardware
- Raspberry Pi Zero 2 W with OV5647 5MP sensor.
- Continuous capture; **no motion detection**.
- Test profiles: 800x600@25/30, 1280x960@30, 1280x720@25/30, 1920x1080@25/30. Offer 720p60 only if a matching sensor mode and sustained FPS are verified on hardware ([TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md) item 1).
- Default profile: **not decided yet.** Chosen after field-of-view, OCR and 24–48 h tests; OV5647 1080p is centre-cropped, 1280x960 keeps the full field of view. See [STATUS.md](STATUS.md), open questions.
- Hardware H.264 through libcamera: Picamera2 as the recorder, `rpicam-vid` for diagnostics only ([RECOMMENDED_STACK.md](RECOMMENDED_STACK.md)). Preview disabled except on demand.
- **Production standard (D8): physical MP4 files split at full wall-clock hours in the configured site timezone.** The first file after a mid-hour start may be shorter; subsequent files normally cover one clock hour. Segment length is not configurable.
- Verify MP4 crash safety, segment integrity and repair with the office MP4 tool. Raw H.264, fragmented MP4 and MPEG-TS are laboratory comparisons only, not production options without the owner's approval.

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
- Bluetooth primary for setup, diagnostics and temporary Internet via technician's phone; validate PAN/tethering behavior by phone model and OS version, Android and iPhone (D5).
- Emergency Wi-Fi access point automatically active during the first **15 minutes after every boot**, regardless of Bluetooth or phone state (D3), with unique SSID and strong unique password.
- AP switches off automatically after 15 minutes.
- **Not decided (Q4 in [STATUS.md](STATUS.md)):** extending the AP from the authenticated panel, or re-opening it later without a reboot (e.g. a documented physical method). These are proposals from the risk audit, not requirements.
- Wi-Fi and Bluetooth can coexist but need field testing for radio/power interference on Zero 2 W.
- Wi-Fi AP should be access-restricted; no default shared fleet-wide password.
- Networking and panel crashes may **never** stop local recording. Single exception: one automatic reboot per power-on period when the camera's own Bluetooth cannot be recovered; a missing phone never counts (D2, D15).

## Bluetooth session flow (D15)
Status: **planned, not implemented; unverified on Zero 2 W and on technicians' phones.** The BLE step conflicts with iPhone support (Q9); the Classic PAN part below is needed in every variant.
- **Purpose:** the phone gives the camera Internet over PAN — first of all for NTP time (D9), later TSP OS sync — and the technician reaches the panel over the same link.
- **Waiting:** BLE advertising with a TSP GATT service (BlueZ GATT server). Advertised name identifies the unit (e.g. Box ID; exact format follows Q2 in [STATUS.md](STATUS.md)).
- **Request:** the phone connects over BLE and writes a defined, authenticated command to the GATT service. Plain BLE advertising, or pairing from the phone's Bluetooth settings, does **not** start PAN on its own — a phone-side client is required. Decided: a **Web Bluetooth** page (D15). Chrome on Android supports Web Bluetooth; Safari on iPhone does not, so the iPhone path is open (Q9). Web Bluetooth requires a secure (HTTPS) page, so the camera cannot serve it over plain `http://`; it must be hosted over HTTPS and available offline on the phone.
- **Session:** on a valid request the camera calls BlueZ `Network1.Connect("nap")` to the phone's Bluetooth tethering. The camera cannot switch tethering on; the technician must enable it on the phone (Android: Bluetooth tethering; iPhone: Personal Hotspot, which Linux reportedly reaches over Bluetooth PAN — to be tested). The camera must learn the phone's Classic address from bonding or from the request itself (Android uses changing BLE addresses) — verify on real phones.
- **Panel over PAN:** a working Internet link on the camera does not prove that the phone's browser can open the camera's panel over the same PAN link. Test on Android and iPhone, including how the technician finds the camera's IP address on the tethering network.
- **Security:** never start PAN for an anonymous BLE connection. Require bonding or another authorisation, rate-limit requests, and optionally keep an allowlist of known technician phones.
- **End:** phone disconnects, or no PAN link within a timeout of a few minutes (value to be set after tests) → back to BLE advertising.
- **Phone unavailable ≠ Bluetooth failure** (D15): no phone, tethering/hotspot off, weak signal, refused authorisation or no NAP → keep recording, keep waiting, rate-limited reconnect attempts; never a reboot.
- **Recovery** (D15), only for a failure of the camera's own Bluetooth confirmed by a self-test (controller or BlueZ not responding, adapter cannot power on or advertise): in `tspcam-connectivity`, independent of `tspcam-capture`, rate-limited, restart Bluetooth service → reset controller → reload Bluetooth driver, for a few rounds, recording continues. Still failing → one automatic reboot of the Pi (recording included). Still failing after that reboot → emergency mode: record only, until physical power-off; no more reboots, radio recovery or extra Wi-Fi. How the one-reboot limit is enforced is open (Q8a). Every step and the recording gap are logged.
- **Proposal, to confirm:** perform the automatic reboot right after the next full-hour file split, so the current MP4 is closed cleanly and only a short gap at the start of the next file is lost.
- **Coexistence:** BLE, Classic PAN and the boot-time Wi-Fi AP share one radio; test them running together during the first 15 minutes after boot.
- **Measure** on Zero 2 W while recording 24/7 (plan in [STATUS.md](STATUS.md), *Pending hardware measurements*). Do not promise energy savings before the measurement.

## Technician UX
- Mobile-first minimal screen: camera ID, RECORDING/ERROR state, recent segment, USB presence/space, RTC/time, temperature, Internet/Bluetooth.
- Configurable resolution, FPS, bitrate preset and target storage. Segment length is fixed by D8.
- Preview on demand, with explicit timeout to reduce CPU/power.
- Safe reboot/shutdown and service controls with confirmation.
- Large plain-language alerts: NO USB, CAMERA ERROR, NOT RECORDING, RTC ERROR.
- A configuration change must be validated and applied at safe segment boundaries where feasible, with rollback on failure.
- Tie each PiCam identity to central TSP OS Unit (single source of truth).

## Acceptance criteria
1. 24-hour unattended recording test at 1280x960@30, 720p30 and 1080p30; count gaps/dropped frames.
2. Measure CPU, temperature, power draw and battery runtime on Zero 2 W.
3. Boot Wi-Fi AP, pair/connect Bluetooth, test phone tethering, verify Wi-Fi auto-off at 15 minutes.
4. Physically remove USB, kill capture process, disconnect phone and cut power; verify recovery behavior and readable previous segments.
5. Export hourly USB logs and replay offline events once connectivity returns.

## Storage duration estimator (technician panel)
- Read actual available free space using filesystem statistics (`statvfs` / `df`) on the configured mounted recording volume, not the nominal USB size.
- Display estimated available recording hours beside every offered recording profile (800x600, 1280x960, 720p, 1080p) and refresh when USB or profile/settings change.
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

## Stamp and OCR compatibility
- **Position and content are decided (D11):** bottom-right corner with date, time, TSP logo and Box number, burned into the frames before encoding.
- The stamp is read by the existing TSP AI analysis, so it is an integration contract, not a cosmetic detail. Every layout must pass OCR regression tests on real footage.
- For reference: the MotionEye frame supplied on 2026-10-08 had a two-line date/time in the lower-left corner and the TSP/site/camera identifier in the lower-right, in white block/pixel-like glyphs with a dark outline. The new layout differs, so TSP AI compatibility must be confirmed — open question in [STATUS.md](STATUS.md).
- Glyph style, size and margins are not decided yet; fix them against a reference sample and OCR tests at 800x600, then provide scaled geometry for 1280x960, 720p and 1080p and verify OCR at each.
- Candidate: Raspberry Pi's official Picamera2 `examples/timestamped_video.py` using `MappedArray` + `pre_callback` before H.264 encode; optimize via cached/pre-rendered glyph overlay to avoid full-frame transformations.
- Avoid FFmpeg decode/drawtext/re-encode of all frames on Zero 2 W; expensive and may not sustain 1080p30.
- Record UTC acquisition time in metadata and render the desired local date/time in the in-frame stamp; validate RTC corrections during capture.
- Acceptance: run TSP AI OCR tests on TSP_Cam frames across timestamps, lighting conditions and resolutions, with MotionEye frames as a baseline. Test sustained FPS with overlay enabled.

## Direct USB write performance
- Zero 2 W USB 2.0 OTG should have ample bandwidth for 3–10 Mb/s H.264 (~0.375–1.25 MB/s), but sustained performance is conditional on actual drive, OTG adapter, mount configuration and stable power.
- Capture directly to mounted USB; do not stage full clips onto the SD card.
- Validate real USB device identity, sustained sequential write performance, storage reliability and behavior on surprise power loss.
- Separate high-priority recording writes from any panel preview, download or health scanning.
- Verify read/write contention while technician browses existing recordings during capture.

## Hardware and operating system notes
- OS (D13): Raspberry Pi OS Lite 32-bit; Bookworm vs Trixie A/B test on a real Zero 2 W with OV5647, then freeze OS/kernel/camera dependency versions after field validation. 64-bit may be benchmarked later.
- Test initially with mains supply and USB; batteries later. Technician phones: Android and iPhone (D5).
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
- For BT PAN on Android and iPhone, test the concrete phone and OS version before treating the connection method as universal.
