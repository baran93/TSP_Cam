# Project status

**Last updated:** 2026-10-16 by Claude, PR #2 (branch `claude/bluetooth-ble-pan`, stacked on PR #1).
Every PR updates this file ([AGENTS.md](../AGENTS.md) §5.3).

## Phase

**Design only (roadmap Phase 0).** No installer, recorder or panel code exists. Nothing has been tested on a Raspberry Pi Zero 2 W yet.

## Current work

| Task | Implementer | Reviewer | State |
|---|---|---|---|
| Collaboration rules and documentation consolidation (PR #1) | Claude | ChatGPT | Reviewed: 5 fixes requested, all applied. Waiting for ChatGPT's re-check and the owner's merge. |
| Bluetooth: BLE discovery → Classic PAN, recovery (D15) (PR #2) | Claude | ChatGPT | PR open, stacked on PR #1 (merge #1 first). Owner decisions on recovery and phones added; waiting for review. |

## Done

- **2026-10-08** — Design documentation written by ChatGPT with the owner: master plan, field requirements, field operation contract, OTA design, technical risk audit, recommended stack, market research.
- **2026-10-16** — Shared rules for both agents ([AGENTS.md](../AGENTS.md)), product brief added ([PROJECT_BRIEF.md](PROJECT_BRIEF.md)), [DECISIONS.md](DECISIONS.md) reduced to decisions in force with history in [DECISION_HISTORY.md](DECISION_HISTORY.md), contradictions between documents removed or flagged below.
- **2026-10-16** — First cross-review: ChatGPT reviewed PR #1 and requested 5 fixes (language as a proposal, technical recommendations vs decisions, branch protection not yet enabled, Wi-Fi wording, brief authorship). Claude applied them in the same PR. The owner confirmed the Wi-Fi boot behaviour (D3).
- **2026-10-16** — Owner accepted the Bluetooth direction: BLE discovery, then Classic PAN, back to BLE after the session (D15). Then decided: one automatic reboot as last resort followed by emergency mode (D2 amended), Web Bluetooth page as the phone client, Android and iPhone support (D5 amended). Open: the Bluetooth path for both platforms (Q9) and the reboot limit (Q8a).

## Open questions for the owner

Found while aligning the documents. Flagged, not resolved; none of them reopens a settled decision.

**Q1. Stamp and TSP AI compatibility.** Position and content are settled (D11: bottom-right, date, time, TSP logo, Box number). The MotionEye reference frame had the date/time in the lower-left corner, and the old requirements called that layout an AI integration contract.
- (a) Will the TSP AI/OCR be adapted to the new position? Who tests it, and on which sample footage?
- (b) Glyph style is undecided: the plan described white text on a semi-transparent dark box, the requirements described white block glyphs with a dark outline (MotionEye style). Suggestion: decide after an OCR test of both.

**Q2. Folder and filename layout on USB.** The documents had two different examples (`TSP-PiCam-004/<date>/<date-time>` and `TSP_Box_030/recordings/`). The field contract says to keep the existing convention (`%Y-%m-%d-%H-%M-%S` under per-unit/per-date folders). Needed: a real path from a current MotionEye USB drive and the exact Box ID format. Hint from ChatGPT's earlier conversations with the owner (PiCam004 settings, **not confirmed as the fleet standard**): `target_dir /media/usb0`, `movie_filename TSP-PiCam004/%Y-%m-%d/%Y-%m-%d-%H-%M-%S`. Related design point: the old architecture suggested giving the file being written a temporary suffix and renaming it on clean close. That was not carried over, because a file cut by power loss would then reach the office under a non-standard name; it is to be settled together with the layout.

**Q3. Default recording profile.** Candidates: 1280×960@30 (full field of view), 1080p30 (centre-cropped on OV5647), 800×600 (legacy). Suggested rule: decide after the field-of-view, OCR and 48 h tests (Gate B). Confirm the rule or set a default.

**Q4. Wi-Fi after the first 15 minutes.** Decided (D3, confirmed 2026-10-16): the AP switches on automatically at every boot, regardless of Bluetooth, and switches off after 15 minutes. Rejected (D15): automatic or periodic Wi-Fi as a Bluetooth fallback, because of battery drain. Still open: after those 15 minutes, should it be possible to (a) extend the AP from the panel, or (b) re-enable it without rebooting the camera with a physical trigger? ChatGPT proposes a **reed switch inside the housing**: holding a magnet to the case switches the AP on for 15 minutes — no holes in the housing, no periodic Wi-Fi, no reboot of a recording camera (hardware change; the GPIO input may draw a tiny current). The risk audit recommends such a recovery path: if the camera's Bluetooth fails at hour 3, today the only way back in is a reboot.

**Q5. Fleet size.** The OTA documents assumed about 200 units; the brief mentions about 400 OV5647 modules. How many Pi units will run TSP_Cam? This affects update rollout and credential distribution.

**Q6. Language.** Proposal written in AGENTS.md §9 (marked as a proposal): repository documents in English, PR descriptions and discussion in Polish. Confirm or change.

**Q7. Product brief.** [PROJECT_BRIEF.md](PROJECT_BRIEF.md) was compiled by ChatGPT from your requirements, not written by you word for word. It ranks second in the precedence list ([AGENTS.md](../AGENTS.md) §4), so please confirm it as the approved product description or say what to change.

**Q8. Resolved 2026-10-16** → D2 amended, D15: recovery of the camera's own Bluetooth without stopping recording; then one automatic reboot; then emergency mode (record only until physical power-off). No periodic Wi-Fi fallback. Clarified after ChatGPT's review: a missing phone, switched-off tethering/hotspot, weak signal or refused authorisation is **not** a Bluetooth failure and never triggers a reboot. Open detail: reboot timing — proposal to reboot right after the next full-hour file split (FIELD_REQUIREMENTS *Bluetooth session flow*).

**Q8a. How to enforce "one automatic reboot".** A Raspberry Pi cannot reliably tell a software reboot from a physical power cut, so "once per power-on period" needs either extra hardware or a different rule. Options: (a) keep "once per power-on period" and add hardware or a tested heuristic to detect a power cycle; (b) at most once per 24 h (by RTC); (c) at most once per survey deployment, reset when a technician connects or confirms the installation. Whatever is chosen must make a reboot loop impossible.

**Q9. Bluetooth path for Android and iPhone — conflict between D15 and D5.** D15 says a Web Bluetooth page sends the BLE request; D5 says Android **and** iPhone must work. Safari on iPhone does not support Web Bluetooth (caniuse, Safari iOS up to 27.2), and Web Bluetooth also requires an HTTPS page, so it cannot be served by the camera itself. On iPhone the BLE step therefore needs an extra app — a third-party browser such as Bluefy or our own app (Ad Hoc / Custom App distribution, Apple Developer account, Mac).

**Both agents recommend** prototyping first the variant that needs no app on either platform: the phone is paired with the camera once using ordinary system pairing; the technician switches on Bluetooth tethering (Android) or Personal Hotspot (iPhone); the camera connects Classic PAN to that trusted phone by itself — more often right after boot, rarely later. Apple supports Bluetooth for Personal Hotspot, and Linux/Raspberry Pi connections to it are reported to work. If this proves stable, the BLE step and the Web Bluetooth page can be dropped; BLE would return only if measurements show a real energy benefit and an iPhone path exists. The Wi-Fi AP at every boot (D3) remains the guaranteed no-app path on both platforms.

Owner to decide: keep D15 as BLE + Web Bluetooth, or change it to Classic PAN with system pairing (BLE deferred). Also open: how phones are authorised (pairing at the office vs in the field, allowlist), and with how many technicians' phones one camera must pair.

Energy context: CNX Software (2021) measured Zero 2 W at about 0.6 W idle and about +55 mW for Wi-Fi connected as a client without traffic (+0.94 W during heavy transfer); camera capture with H.264 was reported at roughly +0.7 W (reader comment, unverified). ChatGPT found an older report for the original Pi Zero W where active Classic Bluetooth added about 0.3 W, similar to active Wi-Fi (different model and conditions). There is **no reliable comparison** of BLE advertising, Classic waiting, active PAN and Wi-Fi AP on Zero 2 W — the measurement below decides; do not quote savings before it.

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
- Classic PAN from the camera to Android Bluetooth tethering and to iPhone Personal Hotspot with system pairing only; reconnect behaviour; several technicians' phones per camera (Q9).
- Panel reachable from the phone's browser over the same PAN link, on Android and iPhone; how the technician finds the camera's IP address.
- BLE → Classic PAN transition, only if BLE stays in D15.
- Self-test that tells a missing phone from a failure of the camera's own Bluetooth; an absent phone or switched-off hotspot must never cause a reboot (D15).
- Automatic-reboot limit as chosen in Q8a; no reboot loop under any failure.
- Current draw on Zero 2 W under identical 24/7 recording, one state at a time: Wi-Fi off + Bluetooth off; BLE advertising; Classic Bluetooth idle/pairable; periodic Classic PAN attempts to a phone that is not there; active Classic PAN; Wi-Fi AP without a client. For each: average W, peaks, time until the technician has access, recording errors, USB drive draw. Owner's earlier reference: about 1.5 W for the whole camera under MotionEye with Wi-Fi.
- Update signing service and read-only delivery for the private repository.
- Objective acceptance limits (maximum gap, frame loss, current draw), set after the baseline hardware test.

## Known risks

The P0/P1 list in [TECHNICAL_RISK_AUDIT.md](TECHNICAL_RISK_AUDIT.md) is current and is not repeated here.

## Next steps

Proposed order; the owner assigns implementer and reviewer for each task.
1. ChatGPT re-checks the fixes in PR #1. The owner answers Q1–Q7 (PR comments are fine; answers can also come later) and merges.
2. ChatGPT reviews PR #2 (merge after #1). The owner decides Q9 (Classic PAN vs BLE) and Q8a (reboot limit).
3. Hardware bring-up on one Zero 2 W + OV5647: run the read-only checklist from [RECOMMENDED_STACK.md](RECOMMENDED_STACK.md) and commit the results. Needs the owner with the hardware.
4. Phase 0 code: Python package skeleton, tests, systemd unit stubs, read-only diagnostics command.
5. Phase 1 recorder MVP: hardware H.264 to hourly MP4 at clock boundaries, autostart on USB, 48 h test.

## PR #3 — Phase 0 Python foundation (proposed, stacked after PR #2)

- Implementer: ChatGPT (GPT-6); reviewer: Claude; owner merges.
- Adds `tspcam status`, periodic read-only diagnostics, localhost-only read-only web page, two systemd services, pilot one-command **local** install, Python unit tests and GitHub Actions CI.
- Explicitly **not implemented**: camera recorder, hourly MP4, autostart capture, RTC writes, external authenticated web panel, BT PAN/Wi-Fi AP, trusted remote GitHub release bootstrap, signed OTA/rollback.
- Next: merge PR #1 then #2, Claude reviews PR #3, pilot check on Zero 2 W, separately implement capture pipeline and signed stable-release delivery. No deployment to live surveys until hardware acceptance tests.
