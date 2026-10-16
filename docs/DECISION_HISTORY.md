# Decision history

> **History only. Never implement anything from this file.** Decisions currently in force are in [DECISIONS.md](DECISIONS.md). See [AGENTS.md](../AGENTS.md) §4–5.

When the owner changes a decision, the previous wording is moved here, newest first.

## 2026-10-16 — Bluetooth recovery and technician phones

The owner decided how the camera behaves when Bluetooth cannot be recovered and that iPhones must be supported (see D2, D5, D15 in [DECISIONS.md](DECISIONS.md)). Previous wording:

### D2 before 2026-10-16 amendment

> Recording never depends on or waits for Bluetooth, Wi-Fi, Internet, the web panel, GitHub or TSP OS. A failure in any of them must not interrupt recording.

Now has one exception: a single automatic reboot per power-on period when Bluetooth cannot be recovered.

### D5 before 2026-10-16 amendment

> Technicians use Android phones.

Now: Android and iPhone must both work. This also reverses the removal recorded in H6 below.

### Proposals not adopted for Bluetooth failure (Q8)

- Wi-Fi AP for 15 minutes as an automatic fallback when Bluetooth fails (Claude). Rejected by the owner: periodic Wi-Fi drains the battery while nobody is at the camera.
- No automatic reboot at all (ChatGPT). The owner chose one reboot, then emergency mode.
- A full reboot after 3 failed attempts, with no limit stated (owner's first idea, 2026-10-16). Replaced by the one-reboot limit and emergency mode.

## 2026-10-16 — Documentation consolidation

On 2026-10-16 the owner confirmed five decisions as settled (stamp, clock-hour MP4, no overwrite/deletion on USB, autostart, Power Down) and agreed a PR-based workflow for Claude, ChatGPT and the owner. The wording below was removed from specification documents because it contradicted a current decision, duplicated a decision with a "superseded" note, or had already been corrected by [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md). Full previous text of every file is in git history at commit `7f6015f`.

### H1. Stamp layout copied from MotionEye

Previously in FIELD_REQUIREMENTS.md, *Compatibility stamp / OCR requirement*:

> - Existing MotionEye overlay format is an AI integration contract, not a cosmetic preference.
> - Reference frame supplied 2026-10-08: lower-left two-line date/time; lower-right TSP/site/camera identifier; white block/pixel-like glyphs with dark outline.
> - Preserve field text, typography, shadow/outline, margins and exact reference pixel coordinates **at 800x600**; verify with original full-resolution reference sample and OCR regression tests.

Replaced by **D11** (bottom-right: date, time, TSP logo, Box number). The MotionEye reference layout is kept as a fact in FIELD_REQUIREMENTS.md. Whether the existing TSP AI/OCR handles the new layout is tracked as an open question in [STATUS.md](STATUS.md).

The two documents also disagreed on stamp style. MASTER_PLAN.md said:

> - Build **in-frame overlay**: bottom right timestamp (OCR-recognizable), TSP logo and Box number, white on dark semi-transparent background. Overlay can render static elements once and update timestamp every second, but compositing may still cost per frame; benchmark on Pi Zero 2 W. Validate OCR across 800x600, 720p and 1080p with real AI; avoid moving stamp without OCR tests.

while FIELD_REQUIREMENTS.md described *white block/pixel-like glyphs with dark outline*. Style is now an open question; position is not.

### H2. Configurable segment length

Previously in MASTER_PLAN.md:

> - Logical recordings: 60min by default, configurable 15/30/60. Evaluate Picamera2 SplittableOutput with PyavOutput for I-frame-safe segment switches (no camera restart); explicitly test power loss recovery, finalized MP4, fragmented MP4/TS alternatives and frame timestamps. If resilience needs shorter physical segments, expose logical 60min grouping in UI and validate the TSP office workflow before changing physical file expectations. Never block capture during browse/download.

and in FIELD_REQUIREMENTS.md, *Technician UX*:

> - Configurable resolution, FPS, bitrate preset, segment length and target storage.

Replaced by **D8** (MP4 split at full wall-clock hours, not configurable).

### H3. Raw H.264 and rpicam-vid segmentation as production options

Previously in FIELD_REQUIREMENTS.md:

> - Prefer hardware H.264 through rpicam/libcamera. Preview disabled except on demand.
> - Prefer MP4 deliverables, but verify crash safety and segment integrity; raw H.264 + remux without re-encoding is an option. Use --inline with rpicam-vid --segment if that backend is selected.

Replaced by **D8** (MP4 deliverable) and [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) (Picamera2 primary; `rpicam-vid` diagnostic only). Raw H.264, fragmented MP4 and MPEG-TS remain laboratory comparisons.

### H4. 1080p30 as target default and optional 720p60

Previously in FIELD_REQUIREMENTS.md:

> - Test profiles: 800x600@25/30, 1280x720@25/30, 1920x1080@25/30. Optionally test 720p60.
> - Target default: 1080p30 if 24-hour reliability, image quality and battery-life testing pass; otherwise 720p30.

Already corrected by TECHNICAL_RISK_AUDIT.md (OV5647 1080p is centre-cropped; evaluate 1280×960@30 first; no unverified 720p60). The default profile is now an open question in [STATUS.md](STATUS.md).

### H5. Trixie as initial OS candidate

Previously in FIELD_REQUIREMENTS.md:

> - Initial OS candidate: Raspberry Pi OS Lite 32-bit Trixie on Pi Zero 2 W. Benchmark vs Lite 64-bit and freeze OS/kernel/camera dependency versions only after successful field validation.

Replaced by **D13** (Lite 32-bit, Bookworm vs Trixie A/B test on real hardware).

### H6. iPhone in tethering validation

Previously in FIELD_REQUIREMENTS.md:

> - Bluetooth primary for setup, diagnostics and temporary Internet via technician's phone; validate PAN/tethering behavior by Android/iPhone version.

Technicians use Android phones (**D5**, product brief).

### H7. Undefined boot policy for invalid time

Previously in MASTER_PLAN.md (end of the time bullet):

> Recording should report TIME INVALID when RTC implausible (define explicit start/block policy before production).

and in ARCHITECTURE.md:

> 4. Detect obviously invalid timestamps and flag them before recording.

Replaced by the confirmed rule in FIELD_OPERATION_SPEC.md: keep recording to preserve evidence, show a warning and log time validity.

### H8. Outdated ARCHITECTURE.md content

ARCHITECTURE.md (2026-10-08) predated later decisions. Key outdated lines:

> Initial capture target remains compatible with the current TSP PiCam use case:
> - 800x600
> - continuous recording
> - 1-hour recording segments
>
> The first implementation should use the current Raspberry Pi camera stack (`rpicam` / libcamera). A Picamera2 implementation can be used where direct programmatic control gives a clear advantage.
>
> Wi-Fi should be disabled in normal field configuration.
>
> Storage layout example: `.../TSP-PiCam-004/2026-10-08/2026-10-08-08-00-00.h264`
>
> A later phase can remux completed H.264 segments to MP4 without re-encoding if required by the office workflow.

Also not carried over: *"Temporary/incomplete files should use a temporary suffix and be atomically renamed after a clean close."* A file cut by power loss would reach the office under a non-standard name; the point is tracked with the USB layout question in [STATUS.md](STATUS.md).

Replaced by **D3**, **D8**, [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) and the component model in [MASTER_PLAN.md](MASTER_PLAN.md). ARCHITECTURE.md is now a short overview that links to those documents instead of repeating them.

### H9. Early service names

Previously in README.md and ARCHITECTURE.md:

> - `tspcam-recorder` — camera capture and file segmentation.
> - `tspcam-api` — lightweight local status/configuration API and web UI.
> - `tspcam-bt` — Bluetooth pairing/PAN connectivity.
> - `tspcam-sync` — offline queue and TSP OS synchronization.
> - `tspcam-health` — storage, camera, RTC, temperature and recording checks.

Replaced by the component model in MASTER_PLAN.md (`tspcam-capture`, `tspcam-control`, `tspcam-agent`, `tspcam-connectivity`, `tspcam-updater`, `tspcam-sync`).

### H10. Fleet size "200"

INSTALL_AND_UPDATES.md and TECHNICAL_RISK_AUDIT.md referred to 200 field cameras; the product brief mentions about 400 OV5647 modules. Wording changed to "hundreds of units"; the actual number of deployed Pi units is an open question in [STATUS.md](STATUS.md).

### H11. Inline "superseded" notes

MASTER_PLAN.md (*Binding field operation requirements*, *Segment rotation decision*) and FIELD_OPERATION_SPEC.md (*Remaining user decision*) carried appended notes repeating the clock-hour decision with "supersedes" wording. They were folded into the main text or replaced by links to DECISIONS.md. No requirement changed.

## 2026-10-08 — Original decision log (verbatim)

The decision log as it stood before consolidation. Entries still in force were carried into [DECISIONS.md](DECISIONS.md); superseded ones are marked in the text itself.

### 2026-10-08 - Replace MotionEye

MotionEye will not be the foundation of the new TSP PiCam software.

Reason:
- unnecessary resource use for a camera whose primary job is continuous recording
- additional moving parts around motion processing and web streaming
- difficult failure diagnosis compared with a purpose-built recorder

### 2026-10-08 - Recording is independent of networking

Bluetooth, Internet, TSP OS and the local panel are secondary services.

A network failure must not interrupt recording.

### 2026-10-08 - Bluetooth instead of field Wi-Fi

Normal field service/setup communication should move from Wi-Fi to Bluetooth.

Primary network model:
- phone = Bluetooth tethering/NAP + Internet gateway
- Pi = PANU client
- Linux network interface = `bnep*`

### 2026-10-08 - Offline first

The camera can operate without Internet.

Events/logs are queued locally and synchronized when technician-phone Internet becomes available.

### 2026-10-08 - Pi Zero 2 W first

The first production target is Raspberry Pi Zero 2 W. Resource usage and dependencies should be evaluated against this device, not a Pi 5 development machine.

### 2026-10-08 - Autostart recording and evidence preservation

On boot, recording must automatically begin to USB once a writable USB volume is present, even with no phone or browser connection. The camera also autostarts on later insertion. Never overwrite or automatically delete any recording. Full/missing USB causes a visible error, with no hidden microSD fallback.

### 2026-10-08 - Keep existing 60-minute physical video workflow

Existing TSP one-hour MP4 files remain the default. The office uses an MP4 repair tool when a file is interrupted by power loss. Do not silently switch production to shorter physical segments or raw H.264; test writer/container on real workflow. **Superseded on 2026-10-08:** the earlier elapsed-3600-second rule was replaced by full wall-clock-hour boundaries. See newest decision below.

### 2026-10-08 - Explicit automatic/manual clock modes

Default AUTO: restore time from RTC and start, synchronize with Internet via technician's Android Bluetooth connection when available, store corrected time to RTC. MANUAL: user can enter date/time; persist setting and prevent NTP/background overwrite. Panel compares camera time to phone time as warning; `Update Time` explicitly changes system clock and RTC and logs correction. Missing RTC communication is an honest alarm.

### 2026-10-08 - One-button full safe shutdown

Authenticated `Power Down` closes/flushes video and filesystems and initiates Raspberry Pi OS poweroff. Explain that power supply/battery may remain physically connected. Technician observes safe-halt indication before unplugging USB.

### 2026-10-08 - Technician installation workflow

Technician checks low-FPS framing preview, live file creation/growth, camera time and RTC status; does not need to start recording manually or play an unfinished MP4.

Canonical behavior specification: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md).


### 2026-10-08 - Superseded: recording segment clock is elapsed 3600 seconds

**Historical decision, superseded later on 2026-10-08.** Previously planned 3600 seconds from recording start. Do not implement this rule; follow the latest wall-clock-aligned decision below.

### 2026-10-08 - FINAL: segment video on full clock hours

**Latest explicit operator decision supersedes the elapsed-3600-second rule above.** Rotate physical MP4 recordings at each full **wall-clock hour** in the camera's configured local timezone. For example, start recording at 14:17 -> first file ends at ~15:00, then 15:00–16:00, 16:00–17:00. The first and shutdown/interrupted files may be shorter. Continue using MP4 and preserve TSP office compatibility. Switch as close as safely possible to hour boundary, at a valid encoder keyframe, without stopping camera capture. Never overwrite or delete older recordings. For clock adjustments, ambiguous DST hours and filename collisions, make uniquely named new segments and log boundaries/time corrections; do not silently extend/overwrite a file. See [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md).
