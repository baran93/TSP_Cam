# TSP_Cam Architecture

## Principles

1. Recording is the highest-priority function.
2. Recording must not depend on Bluetooth, Internet, the web panel or TSP OS.
3. The system is offline-first.
4. Wi-Fi is not required for normal field use.
5. Services should remain small enough for Raspberry Pi Zero 2 W.
6. A camera failure, full USB drive or bad RTC must be reported clearly.
7. Configuration changes must be persistent and auditable.

## Target hardware

Initial target:
- Raspberry Pi Zero 2 W
- Raspberry Pi camera module
- USB storage
- RTC module
- external battery/powerbank

Initial capture target remains compatible with the current TSP PiCam use case:
- 800x600
- continuous recording
- 1-hour recording segments

Exact framerate/bitrate will be measured on real hardware rather than hard-coded as a design assumption.

## Service layout

### tspcam-recorder

Owns the camera.

Responsibilities:
- camera detection
- start/stop capture
- continuous H.264 recording
- time-based segmentation
- safe file close/rename
- write recording state
- automatic recovery after camera or storage errors

The first implementation should use the current Raspberry Pi camera stack (`rpicam` / libcamera). A Picamera2 implementation can be used where direct programmatic control gives a clear advantage.

### tspcam-api

Must never own the recorder lifecycle.

Responsibilities:
- local status page
- configuration
- diagnostics
- one-shot/low-resolution preview on demand
- service actions such as restart recorder or reboot/shutdown

The UI should not continuously decode/process video when nobody is viewing it.

### tspcam-bt

Bluetooth networking and pairing.

Primary mode:
- technician enables Bluetooth tethering on the phone
- Raspberry Pi connects as PANU
- BlueZ creates a `bnep*` network interface
- Pi receives local IP + temporary Internet through the phone
- local API/web panel is reachable over that Bluetooth network

No permanent SIM is required per camera.

Wi-Fi should be disabled in normal field configuration.

### tspcam-sync

Offline-first synchronization.

Local SQLite database stores queued events such as:
- installation/update
- camera health
- recording started/stopped
- USB/storage status
- RTC/time status
- errors
- battery status when hardware support is available

When Internet becomes available through the technician phone, unsent events are uploaded to TSP OS/API and marked as synchronized.

### tspcam-health

Checks:
- camera available
- recorder process alive
- file is actively growing
- USB mounted
- free disk space
- system temperature
- RTC readable
- system time plausible
- Bluetooth state
- Internet/API reachability when connected
- uptime
- last successful sync

Do not assume the camera is always exposed as `/dev/video0`.

## Storage

Suggested layout:

```text
/media/tspcam/
  TSP-PiCam-004/
    2026-10-08/
      2026-10-08-08-00-00.h264
      2026-10-08-09-00-00.h264
```

Temporary/incomplete files should use a temporary suffix and be atomically renamed after a clean close.

A later phase can remux completed H.264 segments to MP4 without re-encoding if required by the office workflow.

## Time

Priority:
1. Network time when Internet is available.
2. Store corrected network time to RTC.
3. On offline boot, restore time from RTC.
4. Detect obviously invalid timestamps and flag them before recording.

## Bluetooth

BlueZ Network API supports PAN roles such as PANU/NAP and exposes the network connection as a Linux interface such as `bnep0`.

Bluetooth is intended for:
- local service panel
- setup/configuration
- sending status/logs
- temporary Internet access through a phone

High-quality continuous live streaming is not a core requirement over Bluetooth. Preview should be low-resolution and on-demand.

## Failure isolation

Examples:
- Phone disconnects -> recording continues.
- TSP OS unavailable -> events remain queued locally.
- Web UI crashes -> recorder continues.
- Bluetooth crashes -> recorder continues.
- USB full/unmounted -> recorder raises critical health state and retries according to policy.
- Camera disappears -> recorder retries and records the failure in local state.

## Future TSP OS integration

Each physical PiCam should map to the central TSP OS Unit record. TSP_Cam should expose stable device identity and health/status instead of maintaining a separate competing source of truth.
