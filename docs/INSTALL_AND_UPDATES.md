# TSP_Cam — Secure Updates and Rollback Specification

Status: **approved design proposal**, not yet implemented. Target: Raspberry Pi Zero 2 W, Raspberry Pi OS Lite, GitHub repository `baran93/TSP_Cam` (currently private).

## 1. Scope and boundaries

This design updates **TSP_Cam application releases** (recorder, API, Bluetooth agent, diagnostics, web UI), NOT the Linux distribution, kernel, firmware or bootloader. OS/firmware upgrades need a separate, explicitly scheduled maintenance workflow and recovery plan. No guarantee of OS rollback from application A/B deployment.

Invariants:
- Recording always has higher priority than updater activity.
- No USB formatting, recording deletion or blanket package upgrades as part of application updates.
- Keep current and last-known-good application version on the microSD.
- Never execute unverified GitHub code as root merely because a branch changed.
- Device config, identity, logs, migration state and recording data live outside release directories.
- All update operations audited with durable timestamps and result codes.
- If the update cannot be safely performed, postpone it instead of forcing downtime.

## 2. On-disk layout

```text
/opt/tspcam/
  releases/v1.0.0/
  releases/v1.1.0/
  current -> releases/v1.0.0
  previous -> releases/v0.9.0
  staging/<version>/
/etc/tspcam/config.yaml
/var/lib/tspcam/identity.json
/var/lib/tspcam/events.db
/var/lib/tspcam/updates.db
/var/lib/tspcam/update-transaction.json
/var/backups/tspcam/
/media/tspcam/<BOX_ID>/...        # recordings; exact layout: open question in docs/STATUS.md
/media/tspcam/<BOX_ID>/logs/
```

`/opt/tspcam` is on the OS microSD, NOT on the USB to be formatted. Keep recorder data outside release directory. Dedicated Unix user for recorder and web service; updater is a separate privileged narrow service.

## 3. Version source, private repo and trust

- Publish versioned GitHub Releases (`vMAJOR.MINOR.PATCH`) with a package, signed manifest, changelog, minimum OS/architecture, schema constraints, size and SHA-256.
- Verify signing key pinned in the device and detached cryptographic signature of manifest; compare expected artifact SHA-256 and size. HTTPS transport alone and unsigned hashes are not adequate authenticity guarantees.
- Device should receive **read-only** access to published assets only; no GitHub write token anywhere in box configuration.
- Private repo: avoid placing a long-lived PAT on hundreds of field cameras. Preferred production architecture: TSP OS / controlled release mirror exposes **only signed release bundles**, using short-lived scoped download authorization. For initial single-device pilot, explicitly provision a read-only token securely with strict file permissions and planned rotation; use this only temporarily.
- No automatic update from `main`; require published stable release and explicit technician confirmation.
- Reject downgrade unless authorized recovery action; reject incompatible architecture/sensor/OS and dangerous schema migrations.
- Protect signing private key outside camera and repo secrets; plan key rotation and emergency revocation.

## 4. Update state machine

```text
IDLE
  -> CHECKING
  -> AVAILABLE
  -> DOWNLOADING
  -> VERIFIED
  -> READY_FOR_CONFIRMATION
  -> WAITING_FOR_SAFE_POINT
  -> ACTIVATING
  -> HEALTH_CHECK
  -> COMMITTED
                 or -> ROLLING_BACK -> ROLLED_BACK
```

- Checking is read-only and may run on technician request with Internet from Android Bluetooth PAN (or approved service Wi-Fi).
- Before downloading: verify free space on OS microSD for old/new releases and backups, memory/temperature, no active format operation, update channel and allowed compatibility.
- Download to staging while recording continues; apply bandwidth/disk-I/O limits to avoid starving recording.
- Verify exact signed release and manifest prior to requesting confirmation.
- UI displays installed/new version, release notes, expected downtime, warnings, mandatory backup readiness. Use separately labeled **Install update** and **Cancel**. Check never implicitly installs.
- On approval, updater acquires exclusive update lock; checks recording health, USB mount identity, no recording/storage error, power stability (as can be measured); optionally refuse unattended/battery update unless technician explicitly opts in.
- Request recorder-controlled safe boundary: finish current segment or safely cut a fresh one, fsync/close completed file, and only then stop encoder. Timeout aborts update; do not kill recorder merely because the update timer elapsed.
- Atomically switch `current` symlink (create temporary symlink then same-filesystem rename); persist journal transaction with fsync. Keep previous untouched.
- Restart selected services via systemd. Web API restart might disconnect technician; state persisted, and reconnect shows progress.
- Verify service readiness plus **real growing recording file and valid codec/sample frames**, reachable local API, USB state, camera health, no crash loop; don't treat process-alive as sufficient. Allow realistic startup grace interval.
- On success, set last-known-good version and mark commit.
- On failure, restore previous pointer and restart prior version; audit failure reason and confirm that old recording resumes.
- At boot, a pre-start recovery service examines update transaction file; interrupted ACTIVATING/HEALTH_CHECK is restored to last-known-good **before** launching recorder.
- Keep at least one last-known-good release + current release; cleanup older releases only after a separate successful health window.

## 5. Storage and data guarantees

- Recordings stored on USB are excluded from package installation and update file operations.
- Never reformat USB, never change USB mount options without an explicit separate operator action.
- Persist local update log on microSD and sync/export to USB/TSP OS when available.
- When possible, write recordings as safely finalized segments so update starts only when a completed segment is flushed. The active segment can still be lost to unexpected physical power removal.
- Backup persistent config and metadata before schema changes. Prefer expand/contract migrations supporting at least one prior software version; irreversible migration must block automatic A/B rollback or require explicit safe fallback procedure.
- Do not pretend application rollback reverses OS package changes, filesystem corruption or physical loss of power.
- Hardware watchdog/voltage and power cutoff integrations are future improvements; updater must not assume stable battery power.

## 6. Security model

- Technician login / pairing required to view update status and explicitly authorize installation.
- CSRF protection for browser updates; API authorization and rate limiting; no arbitrary local path or shell arguments from HTTP.
- HTTP server must NOT run as root. Use a systemd-protected updater service with a limited action API and allowlisted version IDs, verified artifacts, locked-down file permissions.
- Update installation writes never accept arbitrary URL, Git repo, executable or branch specified by web input.
- Use secure BLE/PAN onboarding and emergency AP credentials unique per box.
- Audit: device Unit ID, previous/new versions, requesting technician or client identity, timestamp, artifact hash, update outcome, rollback outcome; off USB.

## 7. UI mock contract

- `Current version: v1.0.0`
- `Stable release: v1.1.0`
- `Check updates` (no state mutation except cache/check log)
- Changelog, size, compatibility and expected pause.
- `Install update` -> confirmation dialog.
- Progress and meaningful status: downloading, verifying, waiting to close file, activating, validating recording, success / rolled back.
- `Revert to previous version` controlled recovery action only if compatible and safely quiesced.
- Technician can leave/reconnect and read the same persisted transaction state.

## 8. Acceptance tests

1. Updating while recording, on USB, with 1080p30 and preview in use: minimal documented gap and no corrupted completed files.
2. No Internet / disconnect in DOWNLOAD -> recording continues and no version switch.
3. Invalid signature / changed hash -> hard reject.
4. Not enough SD space -> clean refusal.
5. Stop updater midway through DOWNLOADING, ACTIVATING, HEALTH_CHECK -> recover consistently (including next boot).
6. Crash new recorder / frozen encoder / no growing file / crash loop -> rollback.
7. Fail REST API or BT during update -> recorder health remains the deciding factor; check UI recovers after reconnect.
8. Unexpected USB disconnect -> no update while recording is unhealthy; do not erase media.
9. Validate reversible/forward-compatible SQLite schema migration and backup restoration.
10. Assert recordings are never touched by update logic and update logs survive format of USB.
11. Staged rollout pilot -> canary -> limited batch -> whole fleet.

## 9. Implementation order

1. Installer and versioned systemd services.
2. Stable release manifest verification and staging.
3. Controlled close/switch/health check.
4. Crash-safe boot recovery and rollback.
5. Technician panel confirmation/progress.
6. Private release distribution via TSP OS with short-lived access, signed content.
7. Fleet staged rollout controls.

Reference: GitHub REST Releases API requires Contents:read for private releases; systemd offers Type=notify and watchdog support.
