# Decisions

## 2026-10-08 - Replace MotionEye

MotionEye will not be the foundation of the new TSP PiCam software.

Reason:
- unnecessary resource use for a camera whose primary job is continuous recording
- additional moving parts around motion processing and web streaming
- difficult failure diagnosis compared with a purpose-built recorder

## 2026-10-08 - Recording is independent of networking

Bluetooth, Internet, TSP OS and the local panel are secondary services.

A network failure must not interrupt recording.

## 2026-10-08 - Bluetooth instead of field Wi-Fi

Normal field service/setup communication should move from Wi-Fi to Bluetooth.

Primary network model:
- phone = Bluetooth tethering/NAP + Internet gateway
- Pi = PANU client
- Linux network interface = `bnep*`

## 2026-10-08 - Offline first

The camera can operate without Internet.

Events/logs are queued locally and synchronized when technician-phone Internet becomes available.

## 2026-10-08 - Pi Zero 2 W first

The first production target is Raspberry Pi Zero 2 W. Resource usage and dependencies should be evaluated against this device, not a Pi 5 development machine.
