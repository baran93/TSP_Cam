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

## 2026-10-08 - Autostart recording and evidence preservation

On boot, recording must automatically begin to USB once a writable USB volume is present, even with no phone or browser connection. The camera also autostarts on later insertion. Never overwrite or automatically delete any recording. Full/missing USB causes a visible error, with no hidden microSD fallback.

## 2026-10-08 - Keep existing 60-minute physical video workflow

Existing TSP one-hour MP4 files remain the default. The office uses an MP4 repair tool when a file is interrupted by power loss. Do not silently switch production to shorter physical segments or raw H.264; test writer/container on real workflow. **Confirmed: files rotate every 3600 seconds elapsed from recording start (not at calendar hour boundaries).**

## 2026-10-08 - Explicit automatic/manual clock modes

Default AUTO: restore time from RTC and start, synchronize with Internet via technician's Android Bluetooth connection when available, store corrected time to RTC. MANUAL: user can enter date/time; persist setting and prevent NTP/background overwrite. Panel compares camera time to phone time as warning; `Update Time` explicitly changes system clock and RTC and logs correction. Missing RTC communication is an honest alarm.

## 2026-10-08 - One-button full safe shutdown

Authenticated `Power Down` closes/flushes video and filesystems and initiates Raspberry Pi OS poweroff. Explain that power supply/battery may remain physically connected. Technician observes safe-halt indication before unplugging USB.

## 2026-10-08 - Technician installation workflow

Technician checks low-FPS framing preview, live file creation/growth, camera time and RTC status; does not need to start recording manually or play an unfinished MP4.

Canonical behavior specification: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md).


## 2026-10-08 - Recording segment clock is elapsed 3600 seconds

**Confirmed by operator:** each normal MP4 recording segment targets 3600 seconds measured from the moment capture starts, matching previous MotionEye `movie_max_time 3600` behavior. Example: recording starts 14:17 -> next segment starts approximately 15:17 (at the next safe video keyframe), not at 15:00. Each subsequent file targets the next 3600 seconds. Use a monotonic elapsed timer: correcting RTC/system wall time must not make a segment shorter, longer, or overwrite another file. Restart/power loss starts a new 3600-second interval with a unique filename. A deliberate Power Down can leave the final segment shorter. Preserve hourly MP4 office workflow; no 5/15-minute physical segmentation without further approval.
