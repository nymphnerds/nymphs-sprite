#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

foundry_root="$(nymphs_sprite_foundry_root || true)"
if [[ -z "${foundry_root}" ]]; then
  echo "ERROR: Sprite Foundry fork was not found. Set NYMPHS_SPRITE_FOUNDRY_ROOT to a checkout containing foundry/cli.py." >&2
  exit 1
fi
foundry_python="$(nymphs_sprite_python_bin)"

preset_id=""
subject_id=""
source_config=""
lora_path=""
lora_trigger=""
lora_scale=""
seed=""
width="1024"
height="1024"
steps="9"
sprite_size="96"
palette_colors="0"
no_check=false
declare -A encoded_parts=()

decode_base64url() {
  python3 - "$1" <<'PY'
from __future__ import annotations

import base64
import sys

value = sys.argv[1].strip()
padding = "=" * ((4 - len(value) % 4) % 4)
print(base64.urlsafe_b64decode((value + padding).encode("ascii")).decode("utf-8"))
PY
}

collect_encoded_arg() {
  local key="$1"
  local value="$2"
  case "${key}" in
    lora-path-b64-*|lora-trigger-b64-*|source-config-b64-*)
      encoded_parts["${key}"]="${value}"
      return 0
      ;;
  esac
  return 1
}

collect_decoded_arg() {
  local prefix="$1"
  local encoded=""
  local index=0
  local key=""
  while true; do
    key="${prefix}-b64-${index}"
    if [[ -z "${encoded_parts[${key}]+set}" ]]; then
      break
    fi
    encoded+="${encoded_parts[${key}]}"
    index=$((index + 1))
  done
  if [[ -n "${encoded}" ]]; then
    decode_base64url "${encoded}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --*=*)
      key="${1%%=*}"
      key="${key#--}"
      value="${1#*=}"
      if collect_encoded_arg "${key}" "${value}"; then
        shift
      else
        case "${key}" in
          preset-id) preset_id="${value}" ;;
          subject-id) subject_id="${value}" ;;
          source-config|config) source_config="${value}" ;;
          lora-path) lora_path="${value}" ;;
          lora-trigger) lora_trigger="${value}" ;;
          lora-scale) lora_scale="${value}" ;;
          seed) seed="${value}" ;;
          width) width="${value}" ;;
          height) height="${value}" ;;
          steps) steps="${value}" ;;
          sprite-size) sprite_size="${value}" ;;
          palette-colors) palette_colors="${value}" ;;
          no-check) no_check=true ;;
          *) echo "ERROR: unsupported argument: --${key}" >&2; exit 2 ;;
        esac
        shift
      fi
      ;;
    --lora-path-b64-*|--lora-trigger-b64-*|--source-config-b64-*)
      key="${1#--}"
      [[ $# -ge 2 ]] || { echo "ERROR: $1 requires a value." >&2; exit 2; }
      collect_encoded_arg "${key}" "${2:-}"
      shift 2
      ;;
    --preset-id)
      [[ $# -ge 2 ]] || { echo "ERROR: --preset-id requires a value." >&2; exit 2; }
      preset_id="${2:-}"
      shift 2
      ;;
    --subject-id)
      [[ $# -ge 2 ]] || { echo "ERROR: --subject-id requires a value." >&2; exit 2; }
      subject_id="${2:-}"
      shift 2
      ;;
    --source-config|--config)
      [[ $# -ge 2 ]] || { echo "ERROR: $1 requires a value." >&2; exit 2; }
      source_config="${2:-}"
      shift 2
      ;;
    --lora-path)
      [[ $# -ge 2 ]] || { echo "ERROR: --lora-path requires a value." >&2; exit 2; }
      lora_path="${2:-}"
      shift 2
      ;;
    --lora-trigger)
      [[ $# -ge 2 ]] || { echo "ERROR: --lora-trigger requires a value." >&2; exit 2; }
      lora_trigger="${2:-}"
      shift 2
      ;;
    --lora-scale)
      [[ $# -ge 2 ]] || { echo "ERROR: --lora-scale requires a value." >&2; exit 2; }
      lora_scale="${2:-}"
      shift 2
      ;;
    --seed|--width|--height|--steps|--sprite-size|--palette-colors)
      [[ $# -ge 2 ]] || { echo "ERROR: $1 requires a value." >&2; exit 2; }
      case "$1" in
        --seed) seed="${2:-}" ;;
        --width) width="${2:-}" ;;
        --height) height="${2:-}" ;;
        --steps) steps="${2:-}" ;;
        --sprite-size) sprite_size="${2:-}" ;;
        --palette-colors) palette_colors="${2:-}" ;;
      esac
      shift 2
      ;;
    --no-check)
      no_check=true
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  nymphs_sprite_foundry_generate.sh --source-config pipeline/chars/goblin_scout.json

Runs Sprite Foundry's canonical Nymphs backend path:
  python3 -m foundry.cli generate-nymphscore
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unsupported argument: $1" >&2
      exit 2
      ;;
  esac
done

decoded="$(collect_decoded_arg "lora-path")"
[[ -n "${decoded}" ]] && lora_path="${decoded}"
decoded="$(collect_decoded_arg "lora-trigger")"
[[ -n "${decoded}" ]] && lora_trigger="${decoded}"
decoded="$(collect_decoded_arg "source-config")"
[[ -n "${decoded}" ]] && source_config="${decoded}"

if [[ -z "${source_config}" ]]; then
  profile_file="${NYMPHS_SPRITE_PROFILES_DIR}/foundry_character_presets.json"
  if [[ ! -f "${profile_file}" ]]; then
    profile_file="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/foundry_character_presets.json"
  fi
  source_config="$(python3 - "${profile_file}" "${preset_id}" "${subject_id}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

profile_file = Path(sys.argv[1])
preset_id = sys.argv[2].strip()
subject_id = sys.argv[3].strip()
try:
    data = json.loads(profile_file.read_text(encoding="utf-8"))
except Exception:
    data = {}

for item in data.get("presets", []):
    if preset_id and item.get("id") == preset_id:
        print(item.get("source_config") or "")
        raise SystemExit(0)
    if subject_id and item.get("subject_id") == subject_id:
        print(item.get("source_config") or "")
        raise SystemExit(0)
print("")
PY
)"
fi

if [[ -z "${source_config}" ]]; then
  echo "ERROR: no Foundry source config was supplied. Choose an imported Foundry preset or pass --source-config." >&2
  exit 2
fi

case "${source_config}" in
  /*)
    config_path="${source_config}"
    ;;
  *)
    config_path="${foundry_root}/${source_config}"
    ;;
esac

if [[ ! -f "${config_path}" ]]; then
  echo "ERROR: Foundry config not found: ${config_path}" >&2
  exit 1
fi

if [[ -f "${NYMPHS_SPRITE_LORA_PRESET_FILE}" ]]; then
  selected_candidate="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_CANDIDATE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_path="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_PATH=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_trigger="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_TRIGGER=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_scale="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_SCALE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  profile_file="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/zimage_turbo_lora_candidates.json"
  if [[ ! -f "${profile_file}" ]]; then
    profile_file="${NYMPHS_SPRITE_PROFILES_DIR}/zimage_turbo_lora_candidates.json"
  fi
  resolved_path="$(python3 - "${profile_file}" "${NYMPHS_SPRITE_LORA_DIR}" "${selected_candidate}" "${selected_path}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

profile_file = Path(sys.argv[1])
lora_dir = Path(sys.argv[2]).expanduser()
candidate = sys.argv[3].strip()
selected_path = Path(sys.argv[4]).expanduser() if sys.argv[4].strip() else None

def candidate_paths(item: dict) -> list[Path]:
    repo_id = str(item.get("repo_id") or "")
    filename = str(item.get("filename") or "")
    library_filename = str(item.get("library_filename") or "")
    paths: list[Path] = []
    if library_filename:
        library_id = Path(library_filename).stem
        paths.append(lora_dir / library_id / library_filename)
        paths.append(lora_dir / library_filename)
    repo_dir = lora_dir / repo_id.replace("/", "--")
    if filename:
        paths.append(repo_dir / filename)
    elif repo_dir.exists():
        paths.extend(sorted(repo_dir.rglob("*.safetensors")))
    return paths

try:
    data = json.loads(profile_file.read_text(encoding="utf-8"))
except Exception:
    data = {"candidates": {}}

item = (data.get("candidates") or {}).get(candidate)
if item:
    for path in candidate_paths(item):
        if path.is_file():
            print(path)
            raise SystemExit(0)
if selected_path and selected_path.is_file():
    print(selected_path)
PY
)"
  [[ -n "${resolved_path}" ]] && selected_path="${resolved_path}"
  [[ -z "${lora_path}" && -n "${selected_path}" ]] && lora_path="${selected_path}"
  [[ -z "${lora_trigger}" && -n "${selected_trigger}" ]] && lora_trigger="${selected_trigger}"
  [[ -z "${lora_scale}" && -n "${selected_scale}" ]] && lora_scale="${selected_scale}"
fi

[[ -n "${lora_trigger}" ]] || lora_trigger="pxlstl"
[[ -n "${lora_scale}" ]] || lora_scale="0.85"

if [[ -n "${lora_path}" && ! -f "${lora_path}" ]]; then
  echo "ERROR: selected LoRA path does not exist: ${lora_path}" >&2
  echo "Run Asset Fetch for Complete Sprite Package, then select a downloaded LoRA." >&2
  exit 1
fi

if command -v curl >/dev/null 2>&1; then
  if ! curl -s -m 5 "${NYMPHS_SPRITE_ZIMAGE_URL%/}/server_info" >/dev/null; then
    echo "Z-Image is not reachable at ${NYMPHS_SPRITE_ZIMAGE_URL}." >&2
    echo "Start Nymphs Image / Z-Image before running Foundry generation." >&2
    exit 1
  fi
elif ! python3 - "${NYMPHS_SPRITE_ZIMAGE_URL}" <<'PY'
from __future__ import annotations

import json
import sys
import urllib.request

url = sys.argv[1].rstrip("/") + "/server_info"
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        json.loads(response.read().decode("utf-8"))
except Exception as exc:
    raise SystemExit(f"ERROR: cannot reach {url}: {exc}")
PY
then
  echo "Z-Image is not reachable at ${NYMPHS_SPRITE_ZIMAGE_URL}." >&2
  echo "Start Nymphs Image / Z-Image before running Foundry generation." >&2
  exit 1
fi

cmd=(
  "${foundry_python}" -m foundry.cli generate-nymphscore
  --config "${config_path}"
  --nymphscore-url "${NYMPHS_SPRITE_ZIMAGE_URL}"
  --lora-trigger "${lora_trigger}"
  --lora-scale "${lora_scale}"
  --width "${width}"
  --height "${height}"
  --steps "${steps}"
  --sprite-size "${sprite_size}"
  --palette-colors "${palette_colors}"
)

if [[ -n "${lora_path}" ]]; then
  cmd+=(--lora-path "${lora_path}")
fi
if [[ -n "${seed}" ]]; then
  cmd+=(--seed "${seed}")
fi
if [[ "${no_check}" == "true" ]]; then
  cmd+=(--no-check)
fi

echo "foundry_root=${foundry_root}"
echo "foundry_config=${config_path}"
echo "zimage_url=${NYMPHS_SPRITE_ZIMAGE_URL}"
echo "lora_path=${lora_path:-auto}"

cd "${foundry_root}"
"${foundry_python}" -m foundry.cli init
"${cmd[@]}"

python3 - "${foundry_root}" "${config_path}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

foundry_root = Path(sys.argv[1])
config_path = Path(sys.argv[2])
config = json.loads(config_path.read_text(encoding="utf-8"))
subject_id = str(config.get("subject_id") or config_path.stem)
matches = sorted(
    (path for path in (foundry_root / "bakeoff").glob(f"{subject_id}_nymphscore_*") if path.is_dir()),
    key=lambda path: path.stat().st_mtime,
    reverse=True,
)
if not matches:
    raise SystemExit(0)
latest = matches[0]
print(f"foundry_run_id={latest.name}")
print(f"foundry_bakeoff_dir={latest}")
for name in ("contact_sheet.png", "raw_inspection.png"):
    path = latest / name
    if path.is_file():
        key = "sprite_contact_sheet" if name == "contact_sheet.png" else "foundry_raw_inspection"
        print(f"{key}={path}")
for path in sorted(latest.glob("*.png")):
    if path.name in {"contact_sheet.png", "raw_inspection.png"} or path.name.endswith("_raw.png"):
        continue
    print(f"output_{path.stem}={path}")
PY
