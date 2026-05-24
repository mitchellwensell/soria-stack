#!/usr/bin/env bash
# hermes-auto-update.sh - fast-forward soria-stack and refresh Hermes skills.
#
# Intended for the VPS Hermes profile. It refuses to touch a dirty checkout,
# uses --ff-only, regenerates Hermes adapters, and restarts the gateway only
# when the checkout actually moved.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PACK_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PACK_DIR"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  exit 0
fi

if ! git config --get remote.origin.url 2>/dev/null | grep -q "soria-stack"; then
  exit 0
fi

if ! git diff --quiet --ignore-submodules -- || ! git diff --cached --quiet --ignore-submodules --; then
  echo "soria-stack Hermes sync: checkout is dirty; skipping auto-update" >&2
  exit 0
fi

before="$(git rev-parse HEAD)"
git fetch --quiet origin main || exit 0
git pull --ff-only --quiet origin main || exit 0
after="$(git rev-parse HEAD)"

"$PACK_DIR/install-hermes.sh" --no-timer >/dev/null

if [ "$before" != "$after" ]; then
  echo "soria-stack Hermes sync: updated ${before:0:8} -> ${after:0:8}" >&2
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user restart hermes-gateway.service >/dev/null 2>&1 || true
  fi
fi
