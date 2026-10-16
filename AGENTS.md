# AGENTS.md — rules for AI agents working on TSP_Cam

This file is the single set of working rules for every AI agent on this repository (currently **Claude** and **ChatGPT**). Agent-specific files such as `CLAUDE.md` only point here. Do not create competing rule files.

## 1. What this project is

TSP_Cam replaces MotionEye on Traffic Survey Partners (TSP) field cameras: Raspberry Pi Zero 2 W (512 MB RAM) + OV5647, recording continuously to USB for MCC/TMC/ANPR surveys and later AI analysis. Hundreds of units, unattended in the field, battery-powered in the target design.

**Current status: design only.** No recorder, installer or panel code exists yet, and nothing has been tested on real hardware. Always state whether something is *implemented*, *planned* or *experimental*, and mark hardware claims as *unverified on Zero 2 W* until a test proves them.

The owner's own product brief (Polish, original wording) is [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md).

## 2. Who does what

| Role | Who | Responsibility |
|---|---|---|
| Owner | baran93 | Makes every decision. Merges every PR. |
| Implementer | one agent per task | Branch, changes, PR, updates `docs/STATUS.md`. |
| Reviewer | the *other* agent | Independent review before the owner merges. |

Current assignment is recorded in [docs/STATUS.md](docs/STATUS.md). Roles may swap from task to task.

The reviewer checks more than document consistency: architecture, failure modes and recovery, resource cost on Zero 2 W (CPU, 512 MB RAM, power), testability, and whether the change actually makes sense in the field.

## 3. Before you start any work

Neither agent can see the other agent's conversations with the owner. **The repository is the only shared memory.** Anything that matters (a decision, a rationale, an open question, a result) must land in the repo, not stay in a chat.

Read, in this order:
1. this file;
2. [docs/STATUS.md](docs/STATUS.md) — what is done, in progress, who works on what, open questions;
3. [docs/DECISIONS.md](docs/DECISIONS.md) — current binding decisions;
4. the specification documents relevant to your task.

## 4. Source-of-truth precedence

When two documents disagree, the higher one wins:

1. [docs/DECISIONS.md](docs/DECISIONS.md) — owner decisions currently in force.
2. [docs/PROJECT_BRIEF.md](docs/PROJECT_BRIEF.md) — owner's product brief.
3. [docs/FIELD_OPERATION_SPEC.md](docs/FIELD_OPERATION_SPEC.md) — confirmed field behaviour.
4. [docs/TECHNICAL_RISK_AUDIT.md](docs/TECHNICAL_RISK_AUDIT.md) — risk findings override premature technical defaults.
5. [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md), [docs/FIELD_REQUIREMENTS.md](docs/FIELD_REQUIREMENTS.md), [docs/INSTALL_AND_UPDATES.md](docs/INSTALL_AND_UPDATES.md), [docs/RECOMMENDED_STACK.md](docs/RECOMMENDED_STACK.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/ROADMAP.md](docs/ROADMAP.md).
6. [docs/MARKET_PROJECT_RESEARCH.md](docs/MARKET_PROJECT_RESEARCH.md) — research, not commitments.

[docs/DECISION_HISTORY.md](docs/DECISION_HISTORY.md) is history only. **Never implement anything from it.**

Precedence is a safety net, not a licence to leave contradictions in place. If you find one, follow rule 5.6.

## 5. Workflow rules

1. **`main` is protected.** No agent writes to `main` directly. Every change goes through a pull request from a branch named `<agent>/<short-task>`, e.g. `claude/recorder-skeleton`, `chatgpt/ota-review-fixes`.
2. **One PR = one logical task.** Group commits by meaning, not one commit per file.
3. **Every PR updates [docs/STATUS.md](docs/STATUS.md)**: completed work, open problems, next steps, current assignment.
4. **Mandatory cross-review.** Implementer opens the PR → the other agent reviews → the owner decides and merges.
5. **Only the owner decides.** When the owner changes a decision, in the same PR:
   - update the entry in `docs/DECISIONS.md`;
   - move the previous wording to `docs/DECISION_HISTORY.md`;
   - align every affected document.
   Never leave "superseded" notes or two conflicting requirements inside a specification document.
6. **Contradictions are flagged, not resolved.** If you find a real contradiction or a requirement that looks wrong, do not pick a side and do not change the requirement. Add it to *Open questions* in `docs/STATUS.md` and mention it in the PR description.
7. **Do not reopen settled decisions** (section 6) unless the owner explicitly asks.
8. **Say when you are not sure.** If you don't know whether something fits Zero 2 W resources, works with OV5647, or behaves as documented upstream, say so and propose a test.

## 6. Settled decisions (do not reopen)

Full wording in [docs/DECISIONS.md](docs/DECISIONS.md). In short:

- **Stamp:** bottom-right corner — date, time, TSP logo, Box number, burned into the video.
- **Recording files:** MP4 split at full wall-clock hours; the first file may be shorter.
- **USB:** never overwrite, never delete recordings automatically; full USB → stop and alarm.
- **Autostart:** recording starts by itself when a working USB drive is detected.
- **Power Down:** closes the recording safely and shuts down the whole Raspberry Pi.
- **Recording is independent** of Bluetooth, Wi-Fi, Internet, the panel and TSP OS.
- **Bluetooth is primary**; emergency Wi-Fi AP only for the first 15 minutes after boot.

## 7. Agent signature

Every commit message and every PR description ends with a signature block:

```text
Agent: Claude | ChatGPT
Model: <model name or ID>
Scope: <one line: what this change covers>
```

The signature describes authorship; it is **not** technical proof of it (commits may be pushed through the owner's account). Tool-specific trailers (e.g. `Co-Authored-By`) may be added after it.

## 8. Engineering principles

From the owner's brief:

1. Recording reliability beats extra features.
2. Minimise CPU, RAM and energy use.
3. Prefer proven libraries and drivers (distro libcamera + Picamera2 + hardware H.264).
4. Design for hundreds of cameras.
5. Test on a real Raspberry Pi Zero 2 W before deployment.
6. Do not violate agreed requirements without prior agreement.
7. Learn from existing open-source and professional traffic-survey systems.
8. Propose improvements, find architecture flaws, anticipate failure modes.
9. Keep implemented, planned and experimental features clearly separated.

Hard constraints: Raspberry Pi OS Lite 32-bit; no Docker; no motion detection or on-device AI; one process owns the camera; no CPU (software) video encoding. See [docs/RECOMMENDED_STACK.md](docs/RECOMMENDED_STACK.md).

## 9. Conventions

- Repository documents are written in **English**. Conversation with the owner and PR descriptions are in **Polish**. The owner's brief stays in its original Polish.
- Dates are ISO (`2026-10-16`). Times in documents are local site time unless marked UTC.
- Keep documents short and non-duplicated: state a fact once and link to it, rather than copying it into several files.
