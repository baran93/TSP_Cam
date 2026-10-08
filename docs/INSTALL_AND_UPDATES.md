# Installation and update design

Status: agreed design, implementation pending.

## Fresh install
- Target: clean Raspberry Pi OS Lite installation on Raspberry Pi Zero 2 W.
- One-command bootstrap after Raspberry Pi OS has booted and network access is available.
- Bootstrap checks OS/architecture, camera model/modes, RTC, storage, available disk space, Internet, needed packages and systemd.
- Present detected environment and require explicit approval before system-wide changes.
- Install runtime, configure independent services, collect diagnostics and report success/failure.
- Never format USB automatically.
- Do not overwrite device identity or existing configuration during reinstall.
- Do not silently erase stored recordings.

## Private GitHub repository
- TSP_Cam is currently private. Unauthenticated raw.githubusercontent.com links cannot fetch its installation script.
- Initial distribution choices to assess: authenticated GitHub release assets with a short-lived token, a separate publicly readable bootstrap, or an authenticated TSP-controlled package mirror.
- Never embed long-lived GitHub PAT or repository write credentials in distributed camera images, scripts or UI.
- Prefer signed/versioned release artifacts over executing arbitrary moving main-branch content as root.
- For production use, pin release version, integrity hash/signature and compatibility metadata.

## Updates from panel
- Show current installed version and latest stable version; separate Check for updates from Install update.
- Pull signed/versioned release metadata, display changelog and required downtime, ask technician to confirm.
- Download and verify before changing active services.
- Preserve persistent configuration, Unit identity, recordings, logs and local event queue.
- Install atomically into versioned application directories; switch current version only after validation.
- Test service health after deployment. Automatically roll back to last known good version on failure.
- Warn that some updates will require a short recording interruption; when feasible switch on a file segment boundary.
- Do not couple updates to USB formatting or OS distribution upgrades.
- Provide recoverable update status and explicit audit trail.
- Support manual/SSH recovery if panel or Bluetooth unavailable.

## Version management
- Use semantic release tags (vX.Y.Z) and a manifest with minimum supported OS/runtime and schema version.
- Schema migrations must be reversible or backward-compatible across at least one release when feasible.
- Avoid automatic background upgrades of camera/OS packages during active recording.
- Roll out first to one pilot device before expanding to the fleet.

## Roadmap
1. Verified clean-image installer and diagnostics.
2. Versioned recording-service MVP.
3. In-panel update check, confirmation, atomic install and rollback.
4. OTA through technician's Android Bluetooth tethering.
