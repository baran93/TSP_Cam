# TSP_Cam — Market and Open-Source Feature Research
Updated 2026-10-08. Competitive research, **not a commitment to implement every feature**. Source product descriptions are vendor claims, not independent performance verification.

## Open-source camera projects

| Project | Confirmed publicly documented functions | Lesson for TSP_Cam | Source |
|---|---|---|---|
| **raspiCamSrv** (signag) | Picamera2 + Flask, CSI/USB module autodetection, main/lores/raw streams, photo/video capture, JPEG low-res streams, snapshot endpoints, capability-dependent AF/zoom/exposure, camera configuration persistence, GPIO control and API. Release notes document race conditions, failed live-view shutdown, lower Pi memory buffer fixes. | Most technically relevant architecture. Borrow **ideas**, not necessarily dependency: one sensor owner, capability-driven UI, low-FPS on demand, minimal buffers and explicit concurrency tests. | https://signag.github.io/raspi-cam-srv/latest/features/ ; https://github.com/signag/raspi-cam-srv/blob/main/docs/ReleaseNotes.md |
| **Kerberos Agent** | Continuous/motion recording, web UI, MP4/H264/H265, primary+secondary streams, low-res MQTT / high-res WebRTC, storage options, REST API, event hooks, modular capture service + web. Raspberry Pi CSI capture may require RTSP sidecar. | Split recording from control plane, explicit stream roles and health; do not import Kubernetes/Docker/RTSP sidecar overhead onto Pi Zero 2 W without need. | https://github.com/kerberos-io/agent |
| **RPi Cam Web Interface** | Camera settings, timelapse, motion, image/video recording, simple install/update scripts; code/docs target older Pi camera stack/Buster-era environment. | Technician UI and operator workflow reference only; do not reuse obsolete MMAL/OMX code. | https://github.com/silvanmelchior/RPi_Cam_Web_Interface |
| **picamctl** (aachtenberg) | H.264 hardware recording/streaming through rpicam-vid, web HLS and VLC transport, MQTT status and systemd. | Learn lightweight systemd controls / telemetry, but do not require HLS or RTSP for low-fps Bluetooth field panel. | https://github.com/aachtenberg/raspberry-pi-camera-control |
| **CamUI** (monkeymademe) | Picamera2/Flask, exposure/AWB/rotation controls, snapshots, gallery/file management, video/snapshot endpoints. | Light mobile-friendly settings and file browser; copy interface concepts not frameworks blindly. | https://github.com/monkeymademe/CamUI |

## Traffic survey vendors and products

| System | What it offers | TSP_Cam relevance | Source |
|---|---|---|---|
| **Miovision Scout Plus** | Portable pole-mounted traffic collection; TMC, volume, speed, pedestrians/bicycles, LTE remote monitoring, alerts including battery/storage, hot-swappable batteries, claimed up to 15 days and <10 min deployment; office video QA and cloud reporting. | Quick field deployment, battery/media alerts, study QA, automatic status/log sync on Internet. | https://miovision.com/scout-plus/ ; https://miovision.com/scout-plus/scout-hardware/ |
| **Tracsis Smart Temporary Surveys / VivaCity** | Battery temporary edge-AI counters for multimodal road user classifications, turning counts, trajectories, cloud live view and remote assurance. | Remote site QA and completeness of study; do NOT try to force the on-device AI stack onto 512MB Zero 2 W. | https://tracsis.com/products/traffic-data/smart-temporary-surveys ; https://tracsis.com/news/smart-temporary-surveys-technical-overview |
| **Telraam S2** | ~10 user classes on edge, cellular 15-minute aggregates, dashboards/API and privacy (no raw video stored). Sensor intended for street segment, not intersections, and has positioning/night limitations. | Minimal metadata sync and QA flags, but **not** a replacement for evidence video. | https://faq.telraam.net/en/article/4/what-and-how-your-telraam-counts-and-does-not-count ; https://telraam.net/en/accuracy-and-precision-of-the-s2-traffic-counter |
| **Viscando OTUS3D** | 3D AI counts pedestrians, cycles and motors with movement, trajectories/speed, interpretation dashboards. | Long-term separate analytics capability. | https://viscando.com/traffic/traffic-counting/ |
| **DataFromSky TrafficSurvey / FLOW** | Analyze fixed, aerial or other video later; trajectories, O/D, TMC, speed, safety, viewer for manual inspection, multi-format exports. | Keep original MP4 and accurate timestamps as reusable data source. Future TSP AI can reprocess same footage. | https://datafromsky.com/trafficsurvey/ ; https://intercom.help/datafromsky/en/articles/3450441-what-is-datafromsky-trafficsurvey-viewer |
| **GoodVision Video Insights** | Video analysis with virtual lines/zones, event definitions, TMC, O/D, peak hour, reports/exports, playback, review/collaboration. | Later TSP OS/AI analysis application separate from PiCam device firmware. | https://goodvisionlive.com/goodvision-video-insights/ ; https://help.goodvisionlive.com/en/articles/3304768-traffic-report-types-in-goodvision |
| **Tracsis AI Portal** | Postprocess survey footage for vehicle/pedestrian categories, speed and movement traces, diagnostics and reports. | Proof that keeping video itself preserves flexibility to do later enhanced surveys. | https://tracsis.com/products/traffic-data/ai-portal |
| **MetroCount RoadPod principle** | Record each axle time and analyze later, with precise source observations retained; older MC5600 EOL. | **Record first, analyse later** and don't discard original evidence. | https://www.metrocount.com/traffic-counters-classifiers/mc5600-vehicle-classifier-system |

## What traffic survey work looks like in 2026
1. Define site/arms/directions, classes, duration, start/end times and deliverables (TMC/MCC, ATR/ATC, classifications, pedestrians/cyclists, O/D/ANPR, speed etc).
2. Install devices and validate their view, lighting, timestamp and actual recording/data availability at roadside.
3. Run a time-bound unattended survey. High-end cellular/edge units provide remote sensor status and sometimes immediate counts; video-first systems retain evidence locally and upload/collect later.
4. Retrieve original data and process with AI / manual or assisted counting. Confirm classification and link/turning counts against sample videos.
5. Export reports by intervals and movement, retain auditability and let office/customer reproduce or inspect counts.

Vendors' accuracy figures are marketing claims tied to specific datasets, site types and definitions; do not transfer these percentages to TSP_Cam.

## New proposed TSP_Cam opportunities (ranked)
**P0, cheap and high value**
- **Pre-install READY checklist** in panel: camera/live frame, recording bytes increasing, RTC plausible vs phone, USB real mount/free hours, voltage/throttle state.
- **Reference snapshot + installation manifest** saved locally with box ID, site/arm optional, timestamp, profile, lens/crop info, actual drive ID and firmware; sync to TSP OS later.
- **Gap/completeness ledger**: record each expected clock-hour MP4 boundary, actual file start/end, size, encoder progress, abnormal resets; never delete/overwrite originals.
- **Visible warnings** for blurred/covered/overexposed/strongly cropped view (start with manual preview or simple metrics; do not claim reliable full AI detection without tests).
- **Camera capability discovery** and protected config presets, low-fps on-demand view, file search, guarded power-down and drive format.
- **No hidden dependencies**: USB local recording works without BT, NTP, phone or API.

**P1, after proof of recorder stability**
- One-click **installation certificate/field report** (Box, time, view snapshot, operating profile, RTC time delta, USB serial/size, status, technician/site).
- Phone-assisted upload of **small proofs only** (snapshot, health, event log, file manifest) via BT PAN/Android Internet, not automatic hours of video.
- **Post-survey completeness analysis** on office/TSP OS: compare expected time window to received MP4 file ranges, checksum or sampled decode results, flag gaps and corrupt segments.
- **Field-safe power/storage warnings** and battery telemetry once compatible hardware is deployed.
- Model-specific calibration and time-sync drift monitoring.

**P2, separate AI/office project**
- Virtual counting lines/zones, TMC/O-D trajectories and reports, QA review and manual correction pipeline.
- Secure customer sharing and data policy for identifiable video.

## Research-informed caution
- Some published projects depend on obsolete Raspbian/MMAL/OMX; use architecture ideas, not obsolete video stack.
- raspiCamSrv release notes document concurrency/race and camera memory issues; **preview never owns or closes capture** in TSP_Cam.
- Relative power/CPU/network measurements and vendor-stated 15-day battery life are not comparable to Zero 2 W+USB until measured.
- Raw video TSP projects and anonymized count-only smart sensors serve different survey needs and have different privacy implications.
