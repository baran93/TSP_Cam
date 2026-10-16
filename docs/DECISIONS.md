# Decisions in force

Only current decisions live here. Only the owner (baran93) makes or changes them. When one changes, the previous wording moves to [DECISION_HISTORY.md](DECISION_HISTORY.md) and every affected document is aligned in the same PR ([AGENTS.md](../AGENTS.md) §5).

Decisions marked **settled** were explicitly re-confirmed by the owner on 2026-10-16. Agents must not reopen them unless the owner asks.

## D1. Replace MotionEye

*Since 2026-10-08.* MotionEye is not the foundation of the new TSP PiCam software. A purpose-built recorder replaces it: less resource use for a camera whose job is continuous recording, fewer moving parts (no motion processing, no web streaming stack), easier failure diagnosis.

## D2. Recording is independent of networking

*Since 2026-10-08.* Recording never depends on or waits for Bluetooth, Wi-Fi, Internet, the web panel, GitHub or TSP OS. A failure in any of them must not interrupt recording.

## D3. Bluetooth first; emergency Wi-Fi AP for 15 minutes after every boot — **settled**

*Since 2026-10-08, boot behaviour re-confirmed by the owner 2026-10-16.* Bluetooth is the primary link: the technician's Android phone provides Bluetooth tethering (NAP), the Pi is the PANU client (`bnep*` interface), giving access to the panel and optionally the phone's Internet.

The emergency Wi-Fi access point switches on automatically at **every boot**, whether or not Bluetooth works or a phone is connected. It stays on for the first 15 minutes and then switches off by itself. It is a standard boot-time window, not a mode triggered by a Bluetooth failure. Per-unit credentials. Recording depends on neither link (D2).

**Not decided:** extending the AP or re-enabling it after the 15 minutes (panel, physical button, …) — open question Q4 in [STATUS.md](STATUS.md). Details: [FIELD_REQUIREMENTS.md](FIELD_REQUIREMENTS.md) *Connectivity*.

## D4. Offline first

*Since 2026-10-08.* The camera works fully without Internet, using its RTC and USB storage. Events and logs are queued locally and synchronised when the technician's phone provides Internet.

## D5. Target hardware and technician phones

*Since 2026-10-08.* First production target: Raspberry Pi Zero 2 W (512 MB RAM) with OV5647 5 MP camera modules, USB recording drive and RTC module. Mains power for testing, battery in the target design. Technicians use Android phones. Resource use is judged on Zero 2 W, not on a faster development Pi.

## D6. Autostart recording — **settled**

*Since 2026-10-08, re-confirmed 2026-10-16.* The camera starts recording by itself once a working, writable USB drive is detected: at boot, or later on insertion without a reboot. It does not wait for a phone, the panel or any network. Missing or failed USB is reported as an error; there is no silent fallback to the system microSD. Details: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) items 1–2, 8.

## D7. No overwriting, no automatic deletion — **settled**

*Since 2026-10-08, re-confirmed 2026-10-16.* Recordings are never overwritten and never deleted automatically. No loop recording, no cleanup to free space. A full USB drive stops capture and raises an alarm. Filenames stay unique even after clock changes or repeated restarts. Details: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) item 3.

## D8. MP4 files split at full wall-clock hours — **settled**

*Since 2026-10-08, re-confirmed 2026-10-16.* Recordings are MP4 files split at each full hour of the camera's configured local time. The first file after start may be shorter (start 14:17 → first file ends about 15:00, then 15:00–16:00, …); a file interrupted by Power Down or failure may also be shorter. The split happens at a suitable H.264 keyframe without stopping capture. Segment length is not configurable. No shorter physical clips or other container in production without the owner's explicit approval. The office repairs files cut by power loss with its MP4 repair tool ("MP4 Fix"). Details: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) items 4–6 and *Clock-hour rotation and clock changes*.

## D9. Clock modes AUTO and MANUAL

*Since 2026-10-08.* **AUTO** (default): restore time from RTC at boot and start recording; when Internet is available through the phone, NTP corrects the clock and the RTC. **MANUAL**: the technician sets date and time; the mode persists and background NTP must not overwrite it. The panel compares phone and camera time and only warns; an explicit *Update time* changes system clock and RTC and is logged. A missing RTC is reported honestly. Details: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) *Timekeeping*.

## D10. Power Down shuts down the whole Pi — **settled**

*Since 2026-10-08, re-confirmed 2026-10-16.* The authenticated *Power Down* button closes the current recording safely, flushes data and filesystems, and powers off the whole Raspberry Pi. It does not claim to disconnect an external battery. Details: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) *Safe Power Down*.

## D11. Stamp in the bottom-right corner — **settled**

*Since 2026-10-16.* The video carries a stamp in the **bottom-right corner** with **date, time, TSP logo and Box number**, burned into the frames before encoding. Compatibility with the existing TSP AI analysis must be verified by OCR tests. Exact glyph style and size are not decided yet ([STATUS.md](STATUS.md), open questions). Details: [FIELD_REQUIREMENTS.md](FIELD_REQUIREMENTS.md) *Stamp and OCR compatibility*.

## D12. Technician installation workflow

*Since 2026-10-08.* The technician powers up the camera, aims it using a low-FPS preview, checks that the current file exists and is growing, checks camera time and RTC status, and leaves it. No manual start of recording, no playing of an unfinished MP4. Details: [FIELD_OPERATION_SPEC.md](FIELD_OPERATION_SPEC.md) *Technician panel*.

## D13. Operating system

*Since 2026-10-08.* Raspberry Pi OS Lite 32-bit. Bookworm or Trixie is chosen after an A/B test on a real Zero 2 W with OV5647; the tested image and dependency versions are then pinned. 64-bit may be benchmarked later. Details: [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md).

## D14. Collaboration workflow

*Since 2026-10-16.* Claude and ChatGPT change the repository only through pull requests; nobody writes to `main` directly. This is an organisational rule; GitHub branch protection is not enabled yet (owner action in [STATUS.md](STATUS.md)). One agent implements, the other reviews in a signed PR comment, the owner decides and merges. Both agents currently act through the owner's GitHub account, so a formal approval from a second account is not possible. Every PR updates [STATUS.md](STATUS.md). Rules: [AGENTS.md](../AGENTS.md).
