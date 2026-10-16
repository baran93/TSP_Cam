#!/usr/bin/env bash
# Pilot-only installation from an already authenticated repository checkout.
# Not an OTA updater. Never touches footage on USB.
set -Eeuo pipefail
export LC_ALL=C
[[ $(id -u) -eq 0 ]] || { echo "Run: sudo bash scripts/install-local.sh" >&2; exit 1; }
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$ROOT/src/tspcam/__init__.py" ]] || { echo "Missing TSP_Cam sources" >&2; exit 1; }
command -v systemctl >/dev/null || { echo "systemd is required" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
python3 -c 'import sys, tomllib; assert sys.version_info >= (3, 11)' || { echo "Python 3.11+ is required" >&2; exit 1; }
# The preview is imported lazily. Install from Raspberry Pi OS apt, not PyPI
# (libcamera bindings must match the installed Raspberry Pi OS).
if ! python3 -c 'from picamera2 import Picamera2' >/dev/null 2>&1; then
  echo "Installing Raspberry Pi OS Picamera2 dependencies for live preview..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends python3-picamera2 python3-pil
fi
# Phase-0 installer must never interrupt an already running production recorder.
if systemctl is-active --quiet tspcam-capture.service; then
  echo "Recording is active: use the future safe release updater, not this installer." >&2
  exit 1
fi
INSTALL_ROOT=/opt/tspcam
install -d -m 0755 "$INSTALL_ROOT" "$INSTALL_ROOT/releases"
if ! id -u tspcam >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/tspcam --shell /usr/sbin/nologin tspcam
fi
# The unprivileged web service needs camera media devices when a preview is open.
for group in video render; do
  if getent group "$group" >/dev/null; then
    usermod -a -G "$group" tspcam
  fi
done
install -d -o tspcam -g tspcam -m 0750 /var/lib/tspcam
# Phase 0 pilot: config is non-secret and CLI runs as pi without sudo.
# Future versions must separate credentials into a private file/service.
install -d -o root -g tspcam -m 0755 /etc/tspcam
if [[ ! -e /etc/tspcam/config.toml ]]; then
  install -o root -g tspcam -m 0644 "$ROOT/packaging/config.example.toml" /etc/tspcam/config.toml
fi
# Repair permissions after upgrading a pilot install created with 0750/0640.
# This applies ONLY to pilot TOML with non-secret settings.
chmod 0755 /etc/tspcam
chmod 0644 /etc/tspcam/config.toml
# Immutable release directories allow retaining the previous version.
CONTENT_HASH="$(cd "$ROOT" && find src/tspcam packaging/systemd -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -c 1-12)"
RELEASE="pilot-$CONTENT_HASH"
DEST="$INSTALL_ROOT/releases/$RELEASE"
STAGE="$(mktemp -d "$INSTALL_ROOT/releases/.stage.XXXXXXXX")"
trap 'rm -rf -- "$STAGE"' EXIT
cp -a -- "$ROOT/src/tspcam" "$STAGE/tspcam"
find "$STAGE/tspcam" -type d -exec chmod 0755 {} +
find "$STAGE/tspcam" -type f -exec chmod 0644 {} +
if [[ ! -d "$DEST" ]]; then
  mv -- "$STAGE" "$DEST"
fi
# mktemp makes STAGE mode 0700. After move, make this directory
# traversable for non-root users, including pi and tspcam.
# Also repairs permissions on a previous pilot install.
chmod 0755 "$DEST"
# Phase 0 services are safe to restart: neither owns a camera/recorder.
systemctl stop tspcam-web.service tspcam-agent.service 2>/dev/null || true
if [[ -L "$INSTALL_ROOT/current" ]]; then
  OLD="$(readlink -- "$INSTALL_ROOT/current")"
  ln -s -- "$OLD" "$INSTALL_ROOT/.previous.$$"
  mv -Tf -- "$INSTALL_ROOT/.previous.$$" "$INSTALL_ROOT/previous"
fi
ln -s -- "releases/$RELEASE" "$INSTALL_ROOT/.current.$$"
mv -Tf -- "$INSTALL_ROOT/.current.$$" "$INSTALL_ROOT/current"
# Do not report a successful install or enable services on a dangling symlink.
if [[ ! -f "$INSTALL_ROOT/current/tspcam/__init__.py" || ! -x "$INSTALL_ROOT/current" ]]; then
  printf 'Install verification failed: current -> %s, expected Python package missing.\n' "$(readlink -- "$INSTALL_ROOT/current" || true)" >&2
  exit 1
fi
install -o root -g root -m 0644 "$ROOT/packaging/systemd/tspcam-agent.service" /etc/systemd/system/tspcam-agent.service
install -o root -g root -m 0644 "$ROOT/packaging/systemd/tspcam-web.service" /etc/systemd/system/tspcam-web.service
cat >/usr/local/bin/tspcam <<'WRAPPER'
#!/bin/sh
cd /opt/tspcam/current || exit 1
exec /usr/bin/python3 -m tspcam "$@"
WRAPPER
chmod 0755 /usr/local/bin/tspcam
systemctl daemon-reload
systemctl enable --now tspcam-agent.service tspcam-web.service
echo "TSP_Cam Phase 0 installed: $RELEASE"
echo "Run: tspcam status"
echo "Web: http://<PI_LAN_IP>:8765 (PILOT ONLY: no login; no WAN port forwarding)"
echo "On-demand JPEG preview enabled (Picamera2); MP4 recording NOT yet implemented."
