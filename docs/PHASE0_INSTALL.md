# Phase 0 installer: read-only application foundation

**Status:** implementation candidate in PR #3, **not** a field recorder or OTA updater. No real Raspberry Pi Zero 2 W hardware validation yet.

## Pilot prerequisites

- Raspberry Pi OS Lite 32-bit Bookworm/Trixie, systemd, Python 3.11+.
- Authorised SSH access from the pilot Pi to the **private** GitHub repository. This requires prior provisioning of SSH credentials (not embedded in the application). Use limited access on pilot devices.
- Raspberry Pi connected to Internet for the initial checkout. This checkout is done by a trusted human, not automatically at camera boot.
- Run installer only on **pilot without a running tspcam-capture.service**. Existing USB footage is neither formatted nor accessed by this installer.

## Installation

From a **trusted checked-out version** of the repository:

```sh
sudo bash scripts/install-local.sh
```

If SSH access to the private repo is already authorised and no checkout exists, this is a **single shell command** to download/install the current `main` for a *pilot only*:

```sh
git clone --depth 1 git@github.com:baran93/TSP_Cam.git /tmp/tspcam-pilot && sudo bash /tmp/tspcam-pilot/scripts/install-local.sh
```

Security warning: the pilot command above trusts the checked-out source and executes its installer as root. **Never deploy it as a fleet OTA command.** The approved fleet design requires signed, versioned release artifacts and a read-only delivery channel; private source code should remain private. This work is scheduled for later phases in [INSTALL_AND_UPDATES.md](INSTALL_AND_UPDATES.md).

## Installed files

- `/opt/tspcam/releases/pilot-<hash>/`: immutable Python source snapshot.
- `/opt/tspcam/current`: atomic link to current; `/opt/tspcam/previous` records preceding version.
- `/etc/tspcam/config.toml`: persistent configuration; only created on first install.
- `/var/lib/tspcam`: persistent state directory; no recordings stored here.
- `/usr/local/bin/tspcam`: CLI wrapper.
- `tspcam-agent.service`: read-only diagnostics journal every minute.
- `tspcam-web.service`: loopback-only HTTP dashboard and JSON status.

## Check after installation

```sh
tspcam status
systemctl status tspcam-agent tspcam-web --no-pager
curl -fsS http://127.0.0.1:8765/api/status
```

For a browser on a workstation, use an SSH forward: `ssh -L 8765:127.0.0.1:8765 pi@<pi-ip>`; open `http://127.0.0.1:8765/` on that workstation.

The dashboard intentionally listens **only on 127.0.0.1**: there is no authentication/TLS yet. Do not expose it over public, Bluetooth, or Wi-Fi networks until a separate PR adds per-device credentials.

## What this PR does **not** implement

No recording, MP4 segmentation, boot capture, stamp, camera live preview, RTC writes, Bluetooth PAN, emergency Wi-Fi AP, Android/iPhone onboarding, authentication, release download, update signing or rollback. `tspcam status` reports only a hardware snapshot, not video health.

Next PR: on-device H.264 and MP4 proof-of-concept using Picamera2, with safe USB mount detection and 48-hour resilience tests. **A real device test is required before production.**
