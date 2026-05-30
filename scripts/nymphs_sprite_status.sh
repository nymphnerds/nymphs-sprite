#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

installed=false
runtime_present=false
data_present=false
version=not-installed
running=false
state=available
health=unavailable
detail="${NYMPHS_SPRITE_MODULE_NAME} is not installed."
selected_lora_path=""
selected_lora_candidate=""
selected_lora_trigger=""
selected_lora_scale=""
lora_count=0
lora_cache_bytes=0
lora_cache_size=0B
lora_files=none
downloaded_loras=none
models_ready=false
assets_ready=false
controlnet_ready=false
depth_models_ready=false
downloaded_models=none
weight_profile_selected=none
weight_profiles_available=none
weight_profiles_downloaded=none
weight_profiles_missing=none
weight_profile_ready=false

if [[ -f "${NYMPHS_SPRITE_MARKER_FILE}" ]]; then
  installed=true
  version="$(head -n 1 "${NYMPHS_SPRITE_MARKER_FILE}" 2>/dev/null || true)"
  [[ -n "${version}" ]] || version=unknown
fi

if [[ -d "${NYMPHS_SPRITE_WORKFLOWS_DIR}" &&
      -d "${NYMPHS_SPRITE_PROFILES_DIR}" &&
      -f "${NYMPHS_SPRITE_UI_DIR}/manager.html" &&
      -f "${NYMPHS_SPRITE_INSTALL_DIR}/nymph.json" &&
      -f "${NYMPHS_SPRITE_INSTALL_DIR}/README.md" ]]; then
  runtime_present=true
fi

if [[ -d "${NYMPHS_SPRITE_OUTPUTS_ROOT}" ||
      -d "${NYMPHS_SPRITE_CONFIG_DIR}" ||
      -d "${NYMPHS_SPRITE_LOGS_DIR}" ]]; then
  data_present=true
fi

if [[ -f "${NYMPHS_SPRITE_LORA_PRESET_FILE}" ]]; then
  selected_lora_candidate="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_CANDIDATE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_path="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_PATH=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_trigger="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_TRIGGER=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_scale="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_SCALE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
fi

PROFILE_FILE="${NYMPHS_SPRITE_PROFILES_DIR}/zimage_turbo_lora_candidates.json"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  PROFILE_FILE="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/zimage_turbo_lora_candidates.json"
fi

if [[ -d "${NYMPHS_SPRITE_CONTROLNET_DIR}/alibaba-pai--Z-Image-Turbo-Fun-Controlnet-Union" ]] &&
   [[ -n "$(find -L "${NYMPHS_SPRITE_CONTROLNET_DIR}/alibaba-pai--Z-Image-Turbo-Fun-Controlnet-Union" -type f \( -name '*.safetensors' -o -name '*.bin' \) -print -quit 2>/dev/null)" ]]; then
  controlnet_ready=true
fi

if [[ -d "${NYMPHS_SPRITE_DEPTH_MODELS_DIR}/depth-anything--Depth-Anything-V2-Small-hf" ]] &&
   [[ -n "$(find -L "${NYMPHS_SPRITE_DEPTH_MODELS_DIR}/depth-anything--Depth-Anything-V2-Small-hf" -type f \( -name '*.safetensors' -o -name '*.bin' \) -print -quit 2>/dev/null)" ]]; then
  depth_models_ready=true
fi

lora_status="$(python3 - "${PROFILE_FILE}" "${NYMPHS_SPRITE_LORA_DIR}" "${NYMPHS_SPRITE_LORA_PRESET_FILE}" <<'PY'
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

profile_file = Path(sys.argv[1])
lora_dir = Path(sys.argv[2]).expanduser()
preset_file = Path(sys.argv[3]).expanduser()

def emit(key: str, value) -> None:
    if value is None or value == "":
        value = "none"
    print(f"{key}={value}")

def clean(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", value).strip("_") or "unknown"

def format_bytes(value: int) -> str:
    size = float(max(value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
        size /= 1024
    return f"{value}B"

try:
    data = json.loads(profile_file.read_text(encoding="utf-8"))
except Exception:
    data = {"candidates": {}}

candidates = data.get("candidates") or {}
available = list(candidates.keys())
selected = ""
selected_path = ""
if preset_file.exists():
    for line in preset_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("NYMPHS_SPRITE_SELECTED_LORA_CANDIDATE="):
            selected = line.split("=", 1)[1].strip()
        elif line.startswith("NYMPHS_SPRITE_SELECTED_LORA_PATH="):
            selected_path = line.split("=", 1)[1].strip()

downloaded: list[str] = []
missing: list[str] = []
files: list[str] = []
seen_paths: set[Path] = set()
total_bytes = 0

for candidate_id, item in candidates.items():
    repo_id = str(item.get("repo_id") or "")
    filename = item.get("filename")
    repo_dir = lora_dir / repo_id.replace("/", "--")
    matches: list[Path] = []
    if filename:
        path = repo_dir / str(filename)
        if path.is_file():
            matches = [path]
    elif repo_dir.exists():
        matches = sorted(path for path in repo_dir.rglob("*.safetensors") if path.is_file())
    if matches:
        downloaded.append(candidate_id)
        path = matches[0]
        files.append(f"{candidate_id}:{path.name}")
        if path not in seen_paths:
            seen_paths.add(path)
            try:
                total_bytes += path.stat().st_size
            except OSError:
                pass
    else:
        missing.append(candidate_id)

if lora_dir.exists():
    for path in sorted(path for path in lora_dir.rglob("*.safetensors") if path.is_file()):
        if path in seen_paths:
            continue
        seen_paths.add(path)
        profile_id = f"custom_{clean(path.stem)}"
        downloaded.append(profile_id)
        files.append(f"{profile_id}:{path.name}")
        try:
            total_bytes += path.stat().st_size
        except OSError:
            pass

if not selected:
    selected = data.get("default") or (downloaded[0] if downloaded else "none")
selected_ready = Path(selected_path).expanduser().is_file() if selected_path else selected in downloaded

emit("lora_count", str(len(seen_paths)))
emit("lora_cache_bytes", str(total_bytes))
emit("lora_cache_size", format_bytes(total_bytes))
emit("lora_files", ",".join(files) if files else "none")
emit("downloaded_loras", ",".join(downloaded) if downloaded else "none")
emit("weight_profile_selected", selected)
emit("weight_profiles_available", ",".join(available) if available else "none")
emit("weight_profiles_downloaded", ",".join(downloaded) if downloaded else "none")
emit("weight_profiles_missing", ",".join(missing) if missing else "none")
emit("weight_profile_ready", "true" if selected_ready else "false")
PY
)"

while IFS='=' read -r key value; do
  case "${key}" in
    lora_count) lora_count="${value}" ;;
    lora_cache_bytes) lora_cache_bytes="${value}" ;;
    lora_cache_size) lora_cache_size="${value}" ;;
    lora_files) lora_files="${value}" ;;
    downloaded_loras) downloaded_loras="${value}" ;;
    weight_profile_selected) weight_profile_selected="${value}" ;;
    weight_profiles_available) weight_profiles_available="${value}" ;;
    weight_profiles_downloaded) weight_profiles_downloaded="${value}" ;;
    weight_profiles_missing) weight_profiles_missing="${value}" ;;
    weight_profile_ready) weight_profile_ready="${value}" ;;
  esac
done <<< "${lora_status}"

downloaded_model_items=()
if [[ "${downloaded_loras}" != "none" ]]; then
  IFS=',' read -ra downloaded_lora_items <<< "${downloaded_loras}"
  for downloaded_lora in "${downloaded_lora_items[@]}"; do
    downloaded_model_items+=("LoRA:${downloaded_lora}")
  done
fi
[[ "${controlnet_ready}" == "true" ]] && downloaded_model_items+=("ControlNet:union")
[[ "${depth_models_ready}" == "true" ]] && downloaded_model_items+=("Depth:depth_anything_v2_small")
if [[ ${#downloaded_model_items[@]} -gt 0 ]]; then
  downloaded_models="$(IFS=,; printf '%s' "${downloaded_model_items[*]}")"
fi

if [[ "${weight_profile_ready}" == "true" ]]; then
  models_ready=true
  assets_ready=true
fi
if [[ -z "${selected_lora_candidate}" || "${selected_lora_candidate}" == "custom" ]]; then
  selected_lora_candidate="${weight_profile_selected}"
fi

if [[ "${installed}" == "true" && "${runtime_present}" == "false" ]]; then
  state=repair_needed
  health=repair-needed
  detail="${NYMPHS_SPRITE_MODULE_NAME} is installed, but module files are missing."
elif [[ "${installed}" == "true" ]]; then
  if [[ "${models_ready}" == "true" ]]; then
    state=installed
    health=ok
    detail="${NYMPHS_SPRITE_MODULE_NAME} is installed. Sprite LoRA cache is ready; start Nymphs Image/Z-Image and generate through the module UI."
  else
    state=model_download_needed
    health=model-download-needed
    detail="Sprite LoRA needs downloading. Use Fetch LoRA to download a Z-Image Turbo-compatible pixel-art LoRA."
  fi
elif [[ "${data_present}" == "true" ]]; then
  detail="${NYMPHS_SPRITE_MODULE_NAME} data remains, but runtime files are not installed."
fi

cat <<STATUS
id=nymphs-sprite
installed=${installed}
runtime_present=${runtime_present}
data_present=${data_present}
version=${version}
running=${running}
state=${state}
health=${health}
install_root=${NYMPHS_SPRITE_INSTALL_DIR}
outputs_root=${NYMPHS_SPRITE_OUTPUTS_ROOT}
config_dir=${NYMPHS_SPRITE_CONFIG_DIR}
logs_dir=${NYMPHS_SPRITE_LOGS_DIR}
models_root=${NYMPHS_SPRITE_MODELS_ROOT}
models_ready=${models_ready}
assets_ready=${assets_ready}
downloaded_models=${downloaded_models}
controlnet_dir=${NYMPHS_SPRITE_CONTROLNET_DIR}
controlnet_ready=${controlnet_ready}
depth_models_dir=${NYMPHS_SPRITE_DEPTH_MODELS_DIR}
depth_models_ready=${depth_models_ready}
workflows_dir=${NYMPHS_SPRITE_WORKFLOWS_DIR}
profiles_dir=${NYMPHS_SPRITE_PROFILES_DIR}
docs_dir=${NYMPHS_SPRITE_DOCS_DIR}
ui_dir=${NYMPHS_SPRITE_UI_DIR}
manager_ui=${NYMPHS_SPRITE_UI_DIR}/manager.html
lora_root=${NYMPHS_SPRITE_LORA_ROOT}
lora_dir=${NYMPHS_SPRITE_LORA_DIR}
downloaded_loras=${downloaded_loras}
lora_count=${lora_count}
lora_cache_bytes=${lora_cache_bytes}
lora_cache_size=${lora_cache_size}
lora_files=${lora_files}
selected_lora_candidate=${selected_lora_candidate}
selected_lora_path=${selected_lora_path}
selected_lora_trigger=${selected_lora_trigger}
selected_lora_scale=${selected_lora_scale}
lora_preset_file=${NYMPHS_SPRITE_LORA_PRESET_FILE}
weight_profile_selected=${weight_profile_selected}
weight_profiles_available=${weight_profiles_available}
weight_profiles_downloaded=${weight_profiles_downloaded}
weight_profiles_missing=${weight_profiles_missing}
weight_profile_ready=${weight_profile_ready}
zimage_url=${NYMPHS_SPRITE_ZIMAGE_URL}
target_model=Tongyi-MAI/Z-Image-Turbo
target_lora_family=zimage
target_controlnet=alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union
target_depth_model=depth-anything/Depth-Anything-V2-Small-hf
generate_entrypoint=${NYMPHS_SPRITE_INSTALL_DIR}/scripts/nymphs_sprite_generate_directions.sh
last_log=${NYMPHS_SPRITE_LOG_FILE}
marker=${NYMPHS_SPRITE_MARKER_FILE}
detail=${detail}
STATUS
