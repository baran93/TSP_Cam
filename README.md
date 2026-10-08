# TSP_Cam

Lightweight Raspberry Pi camera system for TSP, designed to replace MotionEye.

## Goals

- Continuous recording without motion detection overhead.
- Raspberry Pi Zero 2 W first.
- Camera recording must continue even if Bluetooth, API or phone connection fails.
- No Wi-Fi required for normal field operation.
- Bluetooth PAN connection to a technician phone for local control and temporary Internet access.
- Offline-first status/log queue with later sync to TSP OS.
- Recording to USB storage in fixed time segments.
- RTC fallback when Internet time is unavailable.
- Very small local web/API surface for setup, diagnostics and service.

## Initial architecture

```text
Camera Module
     |
     v
tspcam-recorder  ---> USB recordings
     |
     +----> local state / health
                    |
                    v
               tspcam-api
                    |
          Bluetooth PAN (bnep0)
                    |
             Technician phone
                    |
              mobile Internet
                    |
                  TSP OS
```

The recorder is deliberately independent from networking. Losing Bluetooth or Internet must not stop recording.

## Planned services

- `tspcam-recorder` — camera capture and file segmentation.
- `tspcam-api` — lightweight local status/configuration API and web UI.
- `tspcam-bt` — Bluetooth pairing/PAN connectivity.
- `tspcam-sync` — offline queue and TSP OS synchronization.
- `tspcam-health` — storage, camera, RTC, temperature and recording checks.

See `docs/ARCHITECTURE.md` and `docs/ROADMAP.md`.

## Project source of truth

- [MASTER_PLAN](docs/MASTER_PLAN.md) — overall design, implementation order and acceptance gates.
- [FIELD_REQUIREMENTS](docs/FIELD_REQUIREMENTS.md) — field device requirements.
- [INSTALL_AND_UPDATES](docs/INSTALL_AND_UPDATES.md) — secure OTA design.

Status: design only; no deployable installer or camera recorder has yet been implemented.

- [TECHNICAL_RISK_AUDIT](docs/TECHNICAL_RISK_AUDIT.md) — known design risks, corrected assumptions, and preproduction failure tests.
