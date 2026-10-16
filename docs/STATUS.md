# Project status

**Last updated:** 2026-10-16 by Claude, branch `claude/consolidate-docs`.
Every PR updates this file ([AGENTS.md](../AGENTS.md) §5.3).

## Phase

**Design only (roadmap Phase 0).** No installer, recorder or panel code exists. Nothing has been tested on a Raspberry Pi Zero 2 W yet.

## Current work

| Task | Implementer | Reviewer | State |
|---|---|---|---|
| Collaboration rules and documentation consolidation | Claude | ChatGPT | PR open, waiting for review and owner decision |

## Done

- **2026-10-08** — Design documentation written by ChatGPT with the owner: master plan, field requirements, field operation contract, OTA design, technical risk audit, recommended stack, market research.
- **2026-10-16** — Shared rules for both agents ([AGENTS.md](../AGENTS.md)), owner brief added ([PROJECT_BRIEF.md](PROJECT_BRIEF.md)), [DECISIONS.md](DECISIONS.md) reduced to decisions in force with history in [DECISION_HISTORY.md](DECISION_HISTORY.md), contradictions between documents removed or flagged below.

## Open questions for the owner

Found while aligning the documents. Flagged, not resolved; none of them reopens a settled decision.

**Q1. Stamp and TSP AI compatibility.** Position and content are settled (D11: bottom-right, date, time, TSP logo, Box number). The MotionEye reference frame had the date/time in the lower-left corner, and the old requirements called that layout an AI integration contract.
- (a) Will the TSP AI/OCR be adapted to the new position? Who tests it, and on which sample footage?
- (b) Glyph style is undecided: the plan described white text on a semi-transparent dark box, the requirements described white block glyphs with a dark outline (MotionEye style). Suggestion: decide after an OCR test of both.

**Q2. Folder and filename layout on USB.** The documents had two different examples (`TSP-PiCam-004/<date>/<date-time>` and `TSP_Box_030/recordings/`). The field contract says to keep the existing convention (`%Y-%m-%d-%H-%M-%S` under per-unit/per-date folders). Needed: a real path from a current MotionEye USB drive and the exact Box ID format. Related design point: the old architecture suggested giving the file being written a temporary suffix and renaming it on clean close. That was not carried over, because a file cut by power loss would then reach the office under a non-standard name; it is to be settled together with the layout.

**Q3. Default recording profile.** Candidates: 1280×960@30 (full field of view), 1080p30 (centre-cropped on OV5647), 800×600 (legacy). Suggested rule: decide after the field-of-view, OCR and 48 h tests (Gate B). Confirm the rule or set a default.

**Q4. Wi-Fi after the first 15 minutes.** The brief says the AP runs for 15 minutes and switches off. The requirements and risk audit additionally assume the window can be extended from the panel and re-opened by a physical method (button, reed switch, …) if Bluetooth fails later. Confirm both additions and choose the physical method (hardware change).

**Q5. Fleet size.** The OTA documents assumed about 200 units; the brief mentions about 400 OV5647 modules. How many Pi units will run TSP_Cam? This affects update rollout and credential distribution.

**Q6. Language.** Proposed in AGENTS.md: repository documents in English, PR descriptions and discussion in Polish. Confirm or change.

## Owner actions

- **Enable branch protection on `main`** in GitHub repository settings: require a pull request before merging and do not allow bypassing the rule. Until then, "`main` is protected" is only a written rule. Earlier changes reached `main` directly under the owner's account; protection closes that path for both agents.

## Pending hardware measurements

Moved here from MASTER_PLAN so open items live in one place:
- Actual RTC chip, USB adapter/drive models, boot SD capacity.
- OV5647 real field of view and sustained FPS for each profile, especially legacy 800×600.
- MP4 behaviour on power loss: active file repairable with the office MP4 tool, previous files readable.
- Stamp overlay CPU cost at 1080p30; if too expensive, compare GPU/compositor options or simpler burned-in glyphs.
- Android Bluetooth PAN reliability across technicians' phones; Wi-Fi AP and Bluetooth coexistence.
- Update signing service and read-only delivery for the private repository.
- Objective acceptance limits (maximum gap, frame loss, current draw), set after the baseline hardware test.

## Known risks

The P0/P1 list in [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md) is current and is not repeated here.

## Next steps

Proposed order; the owner assigns implementer and reviewer for each task.
1. ChatGPT reviews this PR. The owner answers Q1–Q6 (PR comments are fine) and merges.
2. Hardware bring-up on one Zero 2 W + OV5647: run the read-only checklist from [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) and commit the results. Needs the owner with the hardware.
3. Phase 0 code: Python package skeleton, tests, systemd unit stubs, read-only diagnostics command.
4. Phase 1 recorder MVP: hardware H.264 to hourly MP4 at clock boundaries, autostart on USB, 48 h test.
