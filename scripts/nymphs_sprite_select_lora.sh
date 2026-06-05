#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

PROFILE_FILE="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/zimage_turbo_lora_candidates.json"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  PROFILE_FILE="${NYMPHS_SPRITE_PROFILES_DIR}/zimage_turbo_lora_candidates.json"
fi

candidate=""
lora_path=""
trigger=""
lora_scale=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --candidate|--model|--lora)
      [[ $# -ge 2 ]] || { echo "$1 requires a LoRA candidate id." >&2; exit 2; }
      candidate="${2:-}"
      shift 2
      ;;
    --candidate=*|--model=*|--lora=*)
      candidate="${1#*=}"
      shift
      ;;
    --path|--lora-path)
      [[ $# -ge 2 ]] || { echo "$1 requires a LoRA path." >&2; exit 2; }
      lora_path="${2:-}"
      shift 2
      ;;
    --path=*|--lora-path=*)
      lora_path="${1#*=}"
      shift
      ;;
    --trigger)
      [[ $# -ge 2 ]] || { echo "--trigger requires prompt text." >&2; exit 2; }
      trigger="${2:-}"
      shift 2
      ;;
    --trigger=*)
      trigger="${1#*=}"
      shift
      ;;
    --lora-scale|--scale)
      [[ $# -ge 2 ]] || { echo "$1 requires a numeric scale." >&2; exit 2; }
      lora_scale="${2:-}"
      shift 2
      ;;
    --lora-scale=*|--scale=*)
      lora_scale="${1#*=}"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  nymphs_sprite_select_lora.sh --candidate mks0813_pixel_art
  nymphs_sprite_select_lora.sh --candidate skyasl_pixel_artist
  nymphs_sprite_select_lora.sh --candidate tarn59_pixel_art
  nymphs_sprite_select_lora.sh --path /path/to/lora.safetensors [--trigger TOKEN] [--lora-scale 1]

Selects an already-downloaded sprite LoRA for the next Nymphs Sprite run.
This does not fetch model files.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unsupported argument: $1" >&2
      exit 2
      ;;
  esac
done

nymphs_sprite_ensure_dirs

python3 - "${PROFILE_FILE}" "${NYMPHS_SPRITE_LORA_DIR}" "${NYMPHS_SPRITE_LORA_PRESET_FILE}" "${candidate}" "${lora_path}" "${trigger}" "${lora_scale}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

profile_file = Path(sys.argv[1]).expanduser()
lora_dir = Path(sys.argv[2]).expanduser()
preset_file = Path(sys.argv[3]).expanduser()
candidate = sys.argv[4].strip()
lora_path_arg = sys.argv[5].strip()
trigger_arg = sys.argv[6].strip()
scale_arg = sys.argv[7].strip()


def clean(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", value).strip("_") or "custom"

def candidate_paths(lora_dir: Path, item: dict) -> list[Path]:
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

candidates = data.get("candidates") or {}
repo_id = ""
filename = ""
trigger = trigger_arg
scale = scale_arg
path: Path | None = None

if candidate:
    item = candidates.get(candidate)
    if item:
        repo_id = str(item.get("repo_id") or "")
        filename = str(item.get("filename") or "")
        if not trigger:
            trigger = str(item.get("trigger") or "")
        if not scale:
            scale = str(item.get("recommended_lora_scale") or "")
        for maybe in candidate_paths(lora_dir, item):
            if maybe.is_file():
                path = maybe
                break
    else:
        matches = sorted(lora_dir.rglob("*.safetensors"))
        for maybe in matches:
            if f"custom_{clean(maybe.stem)}" == candidate:
                path = maybe
                repo_id = "custom"
                break
elif lora_path_arg:
    maybe = Path(lora_path_arg).expanduser()
    if maybe.is_file():
        path = maybe
        candidate = f"custom_{clean(maybe.stem)}"
        repo_id = "custom"

if path is None:
    target = candidate or lora_path_arg or "none"
    raise SystemExit(f"ERROR: selected LoRA is not downloaded: {target}")

if not candidate:
    candidate = f"custom_{clean(path.stem)}"
if not repo_id:
    repo_id = "custom"
if not trigger:
    lower_path = str(path).lower()
    trigger = "pxlstl" if "mks0813" in lower_path else ("a pixel art character" if "skyasl" in lower_path else "Pixel art style.")
if not scale:
    scale = "1"

preset_file.parent.mkdir(parents=True, exist_ok=True)
preset_file.write_text(
    "\n".join([
        f"NYMPHS_SPRITE_SELECTED_LORA_REPO={repo_id}",
        f"NYMPHS_SPRITE_SELECTED_LORA_CANDIDATE={candidate}",
        f"NYMPHS_SPRITE_SELECTED_LORA_FILE={path.name}",
        f"NYMPHS_SPRITE_SELECTED_LORA_PATH={path}",
        f"NYMPHS_SPRITE_SELECTED_LORA_TRIGGER={trigger}",
        f"NYMPHS_SPRITE_SELECTED_LORA_SCALE={scale}",
        "",
    ]),
    encoding="utf-8",
)

print(f"lora_selected={candidate}")
print(f"lora_path={path}")
print(f"lora_trigger={trigger}")
print(f"lora_scale={scale}")
print(f"lora_preset_file={preset_file}")
PY
