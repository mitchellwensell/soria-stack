#!/usr/bin/env bash
# install-hermes.sh - expose Soria-stack skills to Hermes without copying them.
#
# Run from a stable soria-stack checkout. The script generates the Hermes
# adapter skills, adds plugins/hermes/skills to ~/.hermes/config.yaml
# skills.external_dirs, and optionally installs a user systemd timer that
# fast-forwards this checkout and restarts Hermes when upstream changes land.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_CONFIG="$HERMES_HOME/config.yaml"
HERMES_SKILLS_DIR="$SCRIPT_DIR/plugins/hermes/skills"
PYTHON_BIN="${PYTHON_BIN:-python3}"
INSTALL_TIMER=1

for arg in "$@"; do
  case "$arg" in
    --no-timer) INSTALL_TIMER=0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

echo "soria-stack Hermes installer"
echo "============================"
echo "Repo:          $SCRIPT_DIR"
echo "Hermes home:   $HERMES_HOME"
echo "Skill dir:     $HERMES_SKILLS_DIR"
echo

if [ ! -d "$HERMES_HOME" ]; then
  echo "ERROR: Hermes home not found: $HERMES_HOME" >&2
  exit 1
fi

if [ ! -f "$HERMES_CONFIG" ]; then
  echo "ERROR: Hermes config not found: $HERMES_CONFIG" >&2
  exit 1
fi

"$PYTHON_BIN" "$SCRIPT_DIR/scripts/sync-hermes-skills.py" >/dev/null

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
import yaml
PY
then
  HERMES_VENV_PY="$HERMES_HOME/hermes-agent/venv/bin/python"
  if [ -x "$HERMES_VENV_PY" ]; then
    PYTHON_BIN="$HERMES_VENV_PY"
  else
    echo "ERROR: PyYAML is required to update $HERMES_CONFIG" >&2
    exit 1
  fi
fi

"$PYTHON_BIN" - "$HERMES_CONFIG" "$HERMES_SKILLS_DIR" <<'PY'
from pathlib import Path
import sys
import yaml

config_path = Path(sys.argv[1]).expanduser()
skills_dir = str(Path(sys.argv[2]).resolve())

cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
skills = cfg.setdefault("skills", {})
external = skills.get("external_dirs") or []
if isinstance(external, str):
    external = [external]
if not isinstance(external, list):
    external = []

normalized = []
seen = set()
for item in external + [skills_dir]:
    item = str(item)
    if item not in seen:
        normalized.append(item)
        seen.add(item)

skills["external_dirs"] = normalized
config_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
print(f"configured skills.external_dirs += {skills_dir}")
PY

if [ "$INSTALL_TIMER" = "1" ] && command -v systemctl >/dev/null 2>&1; then
  UNIT_DIR="$HOME/.config/systemd/user"
  mkdir -p "$UNIT_DIR"

  cat > "$UNIT_DIR/soria-stack-hermes-sync.service" <<EOF
[Unit]
Description=Sync Soria-stack Hermes skills

[Service]
Type=oneshot
ExecStart=$SCRIPT_DIR/scripts/hermes-auto-update.sh
EOF

  cat > "$UNIT_DIR/soria-stack-hermes-sync.timer" <<'EOF'
[Unit]
Description=Run Soria-stack Hermes skill sync hourly

[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
Persistent=true

[Install]
WantedBy=timers.target
EOF

  systemctl --user daemon-reload
  systemctl --user enable --now soria-stack-hermes-sync.timer >/dev/null
  echo "enabled user timer: soria-stack-hermes-sync.timer"
fi

echo
echo "Done. Restart Hermes gateway to load newly generated skill metadata."
