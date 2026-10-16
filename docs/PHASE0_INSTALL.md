# Phase 0 pilot: one-command installation and read-only LAN panel

**Status:** PR #3 on actual pilot Raspberry Pi, **not** a field recorder and not signed OTA.

## One command with temporarily public repository

Only while the owner makes this repository public, and after reviewing the branch:

```sh
d=$(mktemp -d) && curl -fsSL https://api.github.com/repos/baran93/TSP_Cam/tarball/chatgpt/phase0-python-installer | tar -xz --strip-components=1 -C "$d" && sudo bash "$d/scripts/install-local.sh" && tspcam status
```

Does not require Git or a GitHub SSH key. If the repository is private again, unauthenticated downloads fail. Code/history may be copied while public. This shortcut is **only for trusted pilots**; production plans need signed release artifacts.

Requires Raspberry Pi OS Lite, Python 3.11+, systemd, curl and tar. From an already downloaded, trusted checkout, run `sudo bash scripts/install-local.sh`.

## Access from a PC or phone on the same LAN

The pilot read-only dashboard listens on all Pi interfaces (`0.0.0.0:8765`); open `http://<PI_IP>:8765/` from a PC or phone on the same reachable network. Discover IP via `hostname -I` or `ip -4 addr`. Ensure the access point does not enable client isolation.

**Pilot risk:** no authentication or TLS. Anyone with network access can read device status (hostname, USB state, etc.). Do not enable router port forwarding or publicly expose port 8765; this is not production behaviour.

## Verify

```sh
tspcam status
systemctl status tspcam-agent tspcam-web --no-pager
curl -fsS http://127.0.0.1:8765/api/status
ss -ltn | grep ':8765'
```

On disk:
- `/opt/tspcam/releases/pilot-<hash>/` immutable-ish snapshot (release directory mode `0755` so nonroot can traverse).
- `/opt/tspcam/current` atomic symlink to current release; `previous` to prior release.
- `/etc/tspcam/config.toml` preserved between installs. Pilot permissions: directory 0755, file 0644 for non-root CLI. Store **no credentials** in pilot config; move secret values to separate protected storage in future.
- `/var/lib/tspcam` holds persistent state; no USB footage.
- `/usr/local/bin/tspcam` is CLI entrypoint.
- `tspcam-agent.service` and `tspcam-web.service` are diagnostics/status only.

### Resolved pilot issue

The initial script created staging with `mktemp -d` (mode 0700) and moved that directory unchanged into releases; ordinary `pi` user and `tspcam` service therefore could not traverse `/opt/tspcam/current`. Corrected to set release directory mode 0755; also fixed a malformed temporary symlink path in an intervening commit.

This installer does **not** implement capture, recording, MP4, preview, Bluetooth PAN, Wi-Fi AP, real camera settings, RTC updates, auth or fleet OTA. Recorder testing is next.
