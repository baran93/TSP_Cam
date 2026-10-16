# TSP_Cam delivery roadmap

Phase plan only. Binding decisions: [DECISIONS.md](DECISIONS.md); current progress and next steps: [STATUS.md](STATUS.md); document precedence: [AGENTS.md](../AGENTS.md) §4.

## Phase 0 — OS and diagnostics
- [x] Define project architecture and acceptance gates.
- [ ] Compare Bookworm Lite vs Trixie Lite 32-bit on real Zero 2 W/OV5647, then pin the tested image and dependencies.
- [ ] Python package skeleton, service units, installer stub and tests.
- [ ] Detect Pi/sensor, capture modes, RTC, USB, codec capability.
- [ ] Stable Unit/Box identity and typed configuration.

## Phase 1 — Recorder MVP
- [ ] Prove bare hardware H.264 recording without MotionEye.
- [ ] Auto-record at boot/USB insertion without phone or panel; physical MP4 files aligned to full local clock hours (short first file when started mid-hour), compatible with office repair; verify DST/time jumps and no-overwrite behavior.
- [ ] Validate 800x600, **1280x960@30**, 720p30 and 1080p30, including FOV/crop and TSP AI compatibility; reject unverified 720p60 claims.
- [ ] Watchdog checks frame progress and real recording bytes; panel shows active file creation/progression.
- [ ] Persist AUTO/MANUAL time mode, RTC read/write and manual override; warn on phone/camera clock mismatch; record clock changes.
- [ ] Test >48h including active/stalled frames, boot autostart, unplug/reinsert/full USB, no-overwrite clock collisions, MP4 repair, power loss and safe full-system poweroff.

## Phase 2 — Image and live preview
- [ ] Timestamp, TSP logo and Box ID in bottom-right overlay.
- [ ] Verify TSP AI OCR with representative actual footage.
- [ ] Shared low-resolution 1–5 FPS on-demand preview with bounded queues and guaranteed frame-buffer release.
- [ ] Benchmark capture CPU/RAM/temperature and recording continuity.

## Phase 3 — Technician panel and storage
- [ ] Mobile status, settings and camera capability detection.
- [ ] USB and microSD target selection; never silent fallback.
- [ ] Files search/browse/download with pagination.
- [ ] USB filesystem identify, format suggestion and guarded exFAT format.
- [ ] Recording hours estimate for each profile.
- [ ] Simple installation self-test (READY checklist: live frame, file growing, RTC vs phone time, USB mount and free hours, undervoltage) — required by the product brief.
- [ ] One-click diagnostics export and full-system safe Power Down.

## Phase 4 — Field connectivity
- [ ] Bluetooth PAN to Android tethering and iPhone Personal Hotspot, plus temporary Internet (base for D15; needed in any case).
- [ ] BLE advertising + authenticated GATT request from the Web Bluetooth page → Classic PAN → return to BLE (D15). iPhone path per Q9.
- [ ] Bluetooth recovery (D15): retry PAN → restart service → reset controller → reload driver without stopping capture; then one automatic reboot; then emergency mode (record only until power-off). Test the reboot counter across reboots and physical power cycles.
- [ ] Measure Zero 2 W current: BLE waiting vs Classic waiting vs active PAN; owner reviews whether BLE is worth keeping.
- [ ] Wi-Fi AP automatically on for 15 minutes after every boot, with unique credentials (D3).
- [ ] Only if the owner adopts it (Q4): extend or re-enable the AP after 15 minutes without rebooting capture.
- [ ] Protected local access, pairing and disconnection recovery.

## Phase 5 — Installer and OTA
- [ ] One-command supported image installer via authenticated trusted artifacts.
- [ ] Signed GitHub release manifest, staged download and verified integrity.
- [ ] Panel check -> review -> explicit confirm -> safe segment boundary.
- [ ] Health verification, rollback and interrupted-update recovery.
- [ ] No USB wipe and persistent identity/config preservation.

## Phase 6 — Fleet integration
- [ ] TSP OS Unit and installation API.
- [ ] Offline queue, deduplicated event sync and health dashboard.
- [ ] Pilot 3+ devices then staged deployment to fleet.

## Deferred until initial pilot is stable
- Battery telemetry/hot swap and timed power.
- Autofocus/zoom adapter support for future sensor modules.
- AI inference on-device or motion detection (not part of base recorder).

See [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) before choosing build dependencies.

Confirmed technician operation workflow: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md).
