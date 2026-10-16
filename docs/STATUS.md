# Project status

**Last updated:** 2026-10-16 by Claude, PR #2 (branch `claude/bluetooth-ble-pan`, stacked on PR #1).
Every PR updates this file ([AGENTS.md](../AGENTS.md) §5.3).

## Phase

**Design only (roadmap Phase 0).** No installer, recorder or panel code exists. Nothing has been tested on a Raspberry Pi Zero 2 W yet.

## Current work

| Task | Implementer | Reviewer | State |
|---|---|---|---|
| Collaboration rules and documentation consolidation (PR #1) | Claude | ChatGPT | Reviewed: 5 fixes requested, all applied. Waiting for ChatGPT's re-check and the owner's merge. |
| Bluetooth: BLE discovery → Classic PAN, recovery (D15) (PR #2) | Claude | ChatGPT | PR open, stacked on PR #1 (merge #1 first). Waiting for review. |

## Done

- **2026-10-08** — Design documentation written by ChatGPT with the owner: master plan, field requirements, field operation contract, OTA design, technical risk audit, recommended stack, market research.
- **2026-10-16** — Shared rules for both agents ([AGENTS.md](../AGENTS.md)), product brief added ([PROJECT_BRIEF.md](PROJECT_BRIEF.md)), [DECISIONS.md](DECISIONS.md) reduced to decisions in force with history in [DECISION_HISTORY.md](DECISION_HISTORY.md), contradictions between documents removed or flagged below.
- **2026-10-16** — First cross-review: ChatGPT reviewed PR #1 and requested 5 fixes (language as a proposal, technical recommendations vs decisions, branch protection not yet enabled, Wi-Fi wording, brief authorship). Claude applied them in the same PR. The owner confirmed the Wi-Fi boot behaviour (D3).
- **2026-10-16** — Owner accepted the Bluetooth direction: BLE discovery, then Classic PAN, back to BLE after the session (D15). Contested and open parts are Q8 and Q9.

## Open questions for the owner

Found while aligning the documents. Flagged, not resolved; none of them reopens a settled decision.

**Q1. Stamp and TSP AI compatibility.** Position and content are settled (D11: bottom-right, date, time, TSP logo, Box number). The MotionEye reference frame had the date/time in the lower-left corner, and the old requirements called that layout an AI integration contract.
- (a) Will the TSP AI/OCR be adapted to the new position? Who tests it, and on which sample footage?
- (b) Glyph style is undecided: the plan described white text on a semi-transparent dark box, the requirements described white block glyphs with a dark outline (MotionEye style). Suggestion: decide after an OCR test of both.

**Q2. Folder and filename layout on USB.** The documents had two different examples (`TSP-PiCam-004/<date>/<date-time>` and `TSP_Box_030/recordings/`). The field contract says to keep the existing convention (`%Y-%m-%d-%H-%M-%S` under per-unit/per-date folders). Needed: a real path from a current MotionEye USB drive and the exact Box ID format. Hint from ChatGPT's earlier conversations with the owner (PiCam004 settings, **not confirmed as the fleet standard**): `target_dir /media/usb0`, `movie_filename TSP-PiCam004/%Y-%m-%d/%Y-%m-%d-%H-%M-%S`. Related design point: the old architecture suggested giving the file being written a temporary suffix and renaming it on clean close. That was not carried over, because a file cut by power loss would then reach the office under a non-standard name; it is to be settled together with the layout.

**Q3. Default recording profile.** Candidates: 1280×960@30 (full field of view), 1080p30 (centre-cropped on OV5647), 800×600 (legacy). Suggested rule: decide after the field-of-view, OCR and 48 h tests (Gate B). Confirm the rule or set a default.

**Q4. Wi-Fi after the first 15 minutes.** Decided (D3, confirmed 2026-10-16): the AP switches on automatically at every boot, regardless of Bluetooth, and switches off after 15 minutes. Still open: after those 15 minutes, should it be possible to (a) extend the AP from the panel, or (b) re-enable it without rebooting the camera, e.g. with a physical button or reed switch (a hardware change)? The risk audit recommends a recovery path: if Bluetooth fails at hour 3, today the only way back in is a reboot.

**Q5. Fleet size.** The OTA documents assumed about 200 units; the brief mentions about 400 OV5647 modules. How many Pi units will run TSP_Cam? This affects update rollout and credential distribution.

**Q6. Language.** Proposal written in AGENTS.md §9 (marked as a proposal): repository documents in English, PR descriptions and discussion in Polish. Confirm or change.

**Q7. Product brief.** [PROJECT_BRIEF.md](PROJECT_BRIEF.md) was compiled by ChatGPT from your requirements, not written by you word for word. It ranks second in the precedence list ([AGENTS.md](../AGENTS.md) §4), so please confirm it as the approved product description or say what to change.

**Q8. When Bluetooth cannot be recovered.** Agreed: retry PAN → restart Bluetooth service → reset controller → reload driver, all without stopping recording (D15). Not agreed — what after repeated failure (e.g. 3 rounds):
- (a) **Owner's first idea:** full system reboot, recording included.
- (b) **Claude's proposal:** first switch the Wi-Fi AP on for 15 minutes (no recording gap; this also answers part of Q4). Reboot only if Wi-Fi does not come up either (Bluetooth and Wi-Fi share one radio chip, so a hung chip takes both), right after a full-hour file split, at most once per 24 h, logged as a recording gap.
- (c) **ChatGPT's position:** no automatic reboot of a recording camera without a separate owner decision; Bluetooth-level recovery only.

A reboot breaks D2 (no connectivity failure may interrupt recording) and risks a reboot loop if the Bluetooth hardware is dead, so (a) or (b) would mean amending D2. Choose (a), (b), (c) or another rule.

**Q9. Phone-side client for BLE.** Android does not start the BLE → PAN flow from its Bluetooth settings, so technicians need either (a) a small Android app or (b) a Web Bluetooth page in Chrome, installed on the phone beforehand so it works offline. Also: how phones are authorised (pairing at the office vs in the field, allowlist of technician phones, per-box key). Who builds and maintains the client?

## Owner actions

- **Enable branch protection on `main`** in GitHub repository settings (not enabled as of 2026-10-16):
  - require a pull request before merging;
  - **leave "require approvals" off** — both agents work through your account, and GitHub does not let an account approve its own pull request, so required approvals would block every merge;
  - block force pushes and branch deletion, and do not allow bypassing the rules.
  Until this is on, "no direct writes to `main`" is an organisational rule only. Earlier changes reached `main` directly under your account; protection closes that path for both agents.

## Pending hardware measurements

Moved here from MASTER_PLAN so open items live in one place:
- Actual RTC chip, USB adapter/drive models, boot SD capacity.
- OV5647 real field of view and sustained FPS for each profile, especially legacy 800×600.
- MP4 behaviour on power loss: active file repairable with the office MP4 tool, previous files readable.
- Stamp overlay CPU cost at 1080p30; if too expensive, compare GPU/compositor options or simpler burned-in glyphs.
- Android Bluetooth PAN reliability across technicians' phones; Wi-Fi AP and Bluetooth coexistence.
- BLE → Classic PAN transition on technicians' real phones (D15).
- Current draw on Zero 2 W: BLE waiting vs Classic connectable waiting vs active PAN — decides whether BLE is worth the phone-side client.
- Update signing service and read-only delivery for the private repository.
- Objective acceptance limits (maximum gap, frame loss, current draw), set after the baseline hardware test.

## Known risks

The P0/P1 list in [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md) is current and is not repeated here.

## Next steps

Proposed order; the owner assigns implementer and reviewer for each task.
1. ChatGPT re-checks the fixes in PR #1. The owner answers Q1–Q7 (PR comments are fine; answers can also come later) and merges.
2. ChatGPT reviews PR #2 (merge after #1). The owner answers Q8 and Q9.
3. Hardware bring-up on one Zero 2 W + OV5647: run the read-only checklist from [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) and commit the results. Needs the owner with the hardware.
4. Phase 0 code: Python package skeleton, tests, systemd unit stubs, read-only diagnostics command.
5. Phase 1 recorder MVP: hardware H.264 to hourly MP4 at clock boundaries, autostart on USB, 48 h test.
