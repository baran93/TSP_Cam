# TSP_Cam

Lightweight Raspberry Pi camera system for TSP, designed to replace MotionEye on field cameras used for traffic surveys (MCC, TMC, ANPR) and later AI analysis.

**Status: design only.** No installer, recorder or panel has been implemented or tested on hardware yet. Current state and open questions: [docs/STATUS.md](docs/STATUS.md).

## Goals

- Continuous recording, no motion detection.
- Raspberry Pi Zero 2 W + OV5647 first.
- Recording starts by itself on a working USB drive and never depends on Bluetooth, Wi-Fi, Internet, the panel or TSP OS.
- MP4 files split at full wall-clock hours; never overwritten, never deleted automatically.
- In-video stamp in the bottom-right corner: date, time, TSP logo, Box number.
- Bluetooth PAN to the technician's Android phone for the panel and temporary Internet; emergency Wi-Fi AP switches on automatically at every boot and off after 15 minutes.
- RTC keeps time offline; NTP corrects it when the phone provides Internet.
- Offline-first status/log queue with later sync to TSP OS.
- Small authenticated local panel for setup, diagnostics and safe Power Down.

## Architecture at a glance

```text
Camera module
     |
     v
tspcam-capture  ---> USB recordings (MP4, hourly)
     |
     +----> local state / health <---- tspcam-agent
                    |
                    v
             tspcam-control (panel)
                    |
          Bluetooth PAN (bnep0)  /  Wi-Fi AP (first 15 min)
                    |
             Technician phone ---- mobile Internet ---- TSP OS (tspcam-sync)
```

The capture process is deliberately independent from networking. Component details: [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md); overview: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Working on this repository

The project is developed by the owner together with two AI agents (Claude and ChatGPT) through pull requests. **Read [AGENTS.md](AGENTS.md) first.**

## Documents

Start here:
- [AGENTS.md](AGENTS.md) — working rules, roles, source-of-truth precedence.
- [docs/STATUS.md](docs/STATUS.md) — what is done, in progress and waiting for decisions.
- [docs/DECISIONS.md](docs/DECISIONS.md) — decisions in force.
- [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) — product brief (Polish), compiled from the owner's requirements.

Specifications:
- [FIELD_OPERATION_SPEC](docs/FIELD_OPERATION_SPEC.md) — confirmed boot recording, USB retention, time modes and shutdown behaviour.
- [MASTER_PLAN](docs/MASTER_PLAN.md) — overall design, implementation order and acceptance gates.
- [FIELD_REQUIREMENTS](docs/FIELD_REQUIREMENTS.md) — field device requirements.
- [INSTALL_AND_UPDATES](docs/INSTALL_AND_UPDATES.md) — installer and secure OTA design.
- [TECHNICAL_RISK_AUDIT](docs/TECHNICAL_RISK_AUDIT.md) — known risks, corrected assumptions, failure tests.
- [RECOMMENDED_STACK](docs/RECOMMENDED_STACK.md) — researched OS, camera, encoding and reliability choices.
- [ARCHITECTURE](docs/ARCHITECTURE.md) — short system overview.
- [ROADMAP](docs/ROADMAP.md) — delivery phases.

Background:
- [MARKET_PROJECT_RESEARCH](docs/MARKET_PROJECT_RESEARCH.md) — traffic-survey products and Raspberry Pi camera projects (research, not commitments).
- [DECISION_HISTORY](docs/DECISION_HISTORY.md) — superseded decisions (history only).
