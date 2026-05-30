#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

profile=""
confirmed=false
dry_run=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      if [[ $# -lt 2 ]]; then
        echo "--profile requires a LoRA profile id." >&2
        exit 2
      fi
      profile="${2:-}"
      shift 2
      ;;
    --profile=*)
      profile="${1#*=}"
      shift
      ;;
    --yes)
      confirmed=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  nymphs_sprite_delete_models.sh --profile mks0813_pixel_art --yes

Deletes one downloaded Nymphs Sprite LoRA weight from the module LoRA cache.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unsupported argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "${profile}" ]]; then
  echo "ERROR: --profile is required." >&2
  exit 2
fi
if [[ "${confirmed}" != "true" && "${dry_run}" != "true" ]]; then
  echo "ERROR: pass --yes to confirm model deletion." >&2
  exit 1
fi

PROFILE_FILE="${NYMPHS_SPRITE_PROFILES_DIR}/zimage_turbo_lora_candidates.json"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  PROFILE_FILE="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/zimage_turbo_lora_candidates.json"
fi

python3 - "${PROFILE_FILE}" "${NYMPHS_SPRITE_LORA_DIR}" "${NYMPHS_SPRITE_LORA_PRESET_FILE}" "${profile}" "${dry_run}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

profile_file = Path(sys.argv[1])
lora_dir = Path(sys.argv[2]).expanduser().resolve()
preset_file = Path(sys.argv[3]).expanduser()
profile = sys.argv[4].strip()
dry_run = sys.argv[5].lower() == "true"

def clean(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", value).strip("_") or "unknown"

def under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root)
        return True
    except ValueError:
        return False

try:
    data = json.loads(profile_file.read_text(encoding="utf-8"))
except Exception:
    data = {"candidates": {}}

targets: list[Path] = []
item = (data.get("candidates") or {}).get(profile)
if item:
    repo_id = str(item.get("repo_id") or "")
    filename = item.get("filename")
    repo_dir = lora_dir / repo_id.replace("/", "--")
    if filename:
        path = repo_dir / str(filename)
        if path.is_file():
            targets.append(path)
    elif repo_dir.exists():
        targets.extend(sorted(path for path in repo_dir.rglob("*.safetensors") if path.is_file()))
else:
    custom_prefix = "custom_"
    if profile.startswith(custom_prefix) and lora_dir.exists():
        wanted = profile[len(custom_prefix):]
        for path in sorted(path for path in lora_dir.rglob("*.safetensors") if path.is_file()):
            if clean(path.stem) == wanted:
                targets.append(path)
                break

if not targets:
    raise SystemExit(f"ERROR: no downloaded LoRA weight matched profile: {profile}")

deleted: list[str] = []
for target in targets:
    resolved = target.resolve()
    if not under_root(resolved, lora_dir):
        raise SystemExit(f"ERROR: refusing to delete outside LoRA cache: {target}")
    if dry_run:
        print(f"would_delete={resolved}")
    else:
        resolved.unlink()
        deleted.append(str(resolved))
        print(f"deleted={resolved}")

if not dry_run and preset_file.exists():
    text = preset_file.read_text(encoding="utf-8", errors="ignore")
    if any(path in text for path in deleted):
        preset_file.unlink()
        print(f"selected_lora_preset_cleared={preset_file}")

print(f"deleted_profile={profile}")
PY
