# TSP_Cam Roadmap

## Phase 0 - Foundation

- [x] Create repository.
- [x] Define architecture.
- [ ] Add package/service skeleton.
- [ ] Define camera config format.
- [ ] Define stable device identity.
- [ ] Define local SQLite schema.

## Phase 1 - Recorder MVP

Goal: replace MotionEye for the core job.

- [ ] Detect supported camera.
- [ ] Record continuously at initial TSP profile.
- [ ] Split recordings into 1-hour files.
- [ ] Record to USB.
- [ ] Recover after recorder/camera failure.
- [ ] Persist recorder status.
- [ ] Validate recording by checking that the active file grows.

Acceptance test:
- 12+ hour recording test on Pi Zero 2 W with no MotionEye installed.
- power cycle recovery
- USB remove/reinsert failure test
- camera ribbon/module failure test

## Phase 2 - Local diagnostics

- [ ] Lightweight HTTP API.
- [ ] Small mobile-friendly local panel.
- [ ] Camera / recording / USB / RTC / temperature / uptime status.
- [ ] Low-resolution preview only when requested.
- [ ] Restart recorder.
- [ ] Safe shutdown/reboot.

## Phase 3 - Bluetooth

- [ ] Pairing workflow.
- [ ] Connect Raspberry Pi to Android phone Bluetooth tethering.
- [ ] Verify `bnep*` networking.
- [ ] Reach local panel from phone.
- [ ] Verify Internet access through phone.
- [ ] Auto-reconnect policy.
- [ ] Disable Wi-Fi in field image.

## Phase 4 - Offline sync

- [ ] SQLite event queue.
- [ ] Device/install logs.
- [ ] Health events.
- [ ] Sync when Internet appears.
- [ ] Retry/backoff.
- [ ] Deduplication/idempotency.

## Phase 5 - RTC / install workflow

- [ ] RTC read at boot.
- [ ] NTP -> RTC update when Internet exists.
- [ ] Installer phone can confirm/correct camera time.
- [ ] Installation record sent to TSP OS.
- [ ] Camera rename/unit assignment workflow.

## Phase 6 - Power integration

- [ ] Battery telemetry interface.
- [ ] Optional battery percentage/voltage data.
- [ ] Safe low-battery shutdown policy.
- [ ] Timed power controller integration.

## Not in the MVP

- motion detection
- AI vehicle counting
- permanent SIM per camera
- always-on high-resolution live streaming
- large desktop-style MotionEye replacement UI
