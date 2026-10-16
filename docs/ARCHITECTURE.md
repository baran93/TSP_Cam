# TSP_Cam Architecture — overview

Short overview only. Binding behaviour is in [DECISIONS.md](DECISIONS.md) and [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md); the detailed component plan is in [MASTER_PLAN.md](MASTER_PLAN.md); technology choices are in [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md). Status: **design only, not implemented.**

## Principles

1. Recording is the highest-priority function.
2. Recording does not depend on Bluetooth, Wi-Fi, Internet, the web panel or TSP OS (D2).
3. Offline first (D4).
4. Bluetooth is the normal service link. An emergency Wi-Fi AP switches on automatically at every boot and off after 15 minutes (D3); extending or re-enabling it later is undecided (Q4).
5. Everything must fit Raspberry Pi Zero 2 W (512 MB RAM) and minimise CPU and power use.
6. A camera failure, missing or full USB drive, or bad RTC is reported clearly, never hidden.
7. Configuration changes are validated, persistent and auditable.

## Target hardware

Raspberry Pi Zero 2 W, OV5647 camera module (future modules with autofocus or zoom via capability detection), USB recording drive, RTC module. Mains power for testing, battery in the target design (D5).

## Components

Planned systemd services (logical split; may be merged if 512 MB RAM measurements require it). Details: [MASTER_PLAN.md](MASTER_PLAN.md) *Component model*.

| Service | Role |
|---|---|
| `tspcam-capture` | The only camera owner: hardware H.264, hourly MP4 segmentation, burned-in stamp, low-res frames for preview, progress counters, safe stop. |
| `tspcam-control` | Small authenticated HTTP server and mobile web panel: status, configuration, diagnostics, on-demand preview, service actions (restart capture, reboot, Power Down). Never owns the recorder lifecycle; runs as non-root; does not decode or process video when nobody is viewing. |
| `tspcam-agent` | Health probes and durable event log, independent of the browser. |
| `tspcam-connectivity` | BLE advertising for technician discovery, Bluetooth Classic PAN client for the session (D15), Bluetooth recovery, and the emergency Wi-Fi AP (automatic for 15 minutes after every boot). |
| `tspcam-updater` | Narrowly privileged signed-release installer with rollback ([INSTALL_AND_UPDATES.md](INSTALL_AND_UPDATES.md)). |
| `tspcam-sync` | Optional deferred upload to TSP OS. A local SQLite queue holds events (installation/update, health, recording start/stop, USB/storage, RTC/time, errors, battery when supported); unsent events are uploaded when the phone provides Internet and marked as synchronised. |

```text
Camera module
     |
     v
tspcam-capture  ---> USB recordings
     |
     +----> local state / health <---- tspcam-agent
                    |
                    v
             tspcam-control
                    |
   BLE discovery -> Bluetooth PAN (bnep0)  /  emergency Wi-Fi AP (first 15 min)
                    |
             Technician phone ---- mobile Internet ---- TSP OS
```

## Health checks (`tspcam-agent`)

Process liveness alone is not enough ([TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md) item 2). Check:
- fresh camera frames and encoder output; the active file is actually growing;
- USB mounted on the expected device, writable, free space;
- RTC readable, system time plausible, clock mode;
- CPU temperature, RAM, undervoltage/throttling, USB disconnects;
- Bluetooth state, Internet/TSP OS reachability when connected, last successful sync, uptime.

Do not assume the camera is always `/dev/video0`.

## Storage and time

- Recording files, retention and naming: D6–D8 and [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) items 1–8. The exact folder and filename layout on USB is an open question in [STATUS.md](STATUS.md).
- Clock: D9 and [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) *Timekeeping*. With invalid time the camera keeps recording to preserve evidence, shows a warning and logs time validity.

## Bluetooth

While waiting, the camera advertises over BLE. The technician's phone sends an authenticated request over BLE; the camera then connects to the phone's Bluetooth tethering as PANU, and returns to BLE when the session ends (D15; flow and constraints in [FIELD_REQUIREMENTS.md](FIELD_REQUIREMENTS.md) *Bluetooth session flow*). BlueZ Network API supports PAN roles (PANU/NAP) and exposes the link as a Linux interface such as `bnep0`; the Pi gets a local IP and temporary Internet, and the panel is reachable over that link. No permanent SIM per camera.

Bluetooth carries the panel, setup, status/logs and temporary Internet. Continuous high-quality live video is not a goal; preview is low-resolution and on demand.

## Failure isolation

- Phone disconnects → recording continues.
- TSP OS unavailable → events stay queued locally.
- Panel or Bluetooth crashes → recording continues.
- USB full or unmounted → critical health state, alarm, no writes to microSD (D6, D7).
- Camera disappears → capture retries with bounded backoff and records the gap.

## TSP OS integration (future)

Each physical camera maps to a TSP OS Unit record. TSP_Cam exposes a stable device identity and health/status rather than keeping a competing source of truth.
