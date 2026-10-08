# TSP_Cam delivery roadmap

Authoritative specifications: [MASTER_PLAN](MASTER_PLAN.md), [FIELD_REQUIREMENTS](FIELD_REQUIREMENTS.md), [INSTALL_AND_UPDATES](INSTALL_AND_UPDATES.md).

## Phase 0 — OS and diagnostics
- [x] Define project architecture and acceptance gates.
- [ ] Compare Bookworm Lite vs Trixie Lite 32-bit on real Zero 2 W/OV5647, then pin the tested image and dependencies.
- [ ] Python package skeleton, service units, installer stub and tests.
- [ ] Detect Pi/sensor, capture modes, RTC, USB, codec capability.
- [ ] Stable Unit/Box identity and typed configuration.

## Phase 1 — Recorder MVP
- [ ] Prove bare hardware H.264 recording without MotionEye.
- [ ] Detect/mount correct USB; hourly finalized segments.
- [ ] Validate 800x600, **1280x960@30**, 720p30 and 1080p30, including FOV/crop and TSP AI compatibility.
- [ ] Watchdog checks frame progress and real recording bytes.
- [ ] Persistent event journal and RTC time validation.
- [ ] Test >48h including active/stalled frame detection, reboot, failed USB, power loss, FPS timestamp checks and disk corruption.

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
- [ ] One-click diagnostics export.

## Phase 4 — Field connectivity
- [ ] Android Bluetooth PAN plus temporary Internet.
- [ ] 15-minute per-boot Wi-Fi AP with unique credentials **plus service recovery after 15min without rebooting capture**.
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
