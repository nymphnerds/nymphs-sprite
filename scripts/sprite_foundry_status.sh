#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

installed=false
runtime_present=false
data_present=false
version="not-installed"
running=false
state="available"
health="unavailable"
detail="${SPRITE_FOUNDRY_MODULE_NAME} is not installed."
controlnet_ready=false
map_depth_anything_ready=false
map_midas_ready=false
map_models_ready=false
weight_profiles_available="${SPRITE_FOUNDRY_CONTROLNET_PROFILE},${SPRITE_FOUNDRY_LORA_MKS0813_PROFILE},${SPRITE_FOUNDRY_LORA_SKYASL_PROFILE},${SPRITE_FOUNDRY_LORA_TARN59_PROFILE},${SPRITE_FOUNDRY_MAP_DEPTH_ANYTHING_PROFILE},${SPRITE_FOUNDRY_MAP_MIDAS_PROFILE},${SPRITE_FOUNDRY_MAP_ALL_PROFILE}"
weight_profiles_downloaded="none"
weight_profiles_missing="${SPRITE_FOUNDRY_CONTROLNET_PROFILE}"
models_ready=false
zimage_installed=false
zimage_running=false
zimage_models_ready=false
zimage_health=unknown
zimage_state=unknown
zimage_detail=unknown
zimage_weight_profile_selected=none
zimage_weight_profile_ready=false
zimage_nunchaku_rank=32
zimage_nunchaku_precision=auto
zimage_downloaded_models=none
zimage_downloaded_weights=none
zimage_missing_weights=none
zimage_hf_cache_dir="${SPRITE_FOUNDRY_HF_CACHE_DIR}"
lora_choices=none
downloaded_loras=none
selected_lora_candidate=""
selected_lora_path=""
selected_lora_trigger="pxlstl"
selected_lora_scale="1"

if sprite_foundry_controlnet_ready; then
  controlnet_ready=true
fi
if sprite_foundry_depth_anything_ready; then
  map_depth_anything_ready=true
fi
if sprite_foundry_midas_ready; then
  map_midas_ready=true
fi
if [[ "${map_depth_anything_ready}" == "true" && "${map_midas_ready}" == "true" ]]; then
  map_models_ready=true
fi

lora_status="$(
  python3 - "${SPRITE_FOUNDRY_LORA_ROOT}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

lora_root = Path(sys.argv[1]).expanduser()
candidates = {
    "mks0813--z-image-turbo-pixel-art-lora": {
        "profile": "nymphs_sprite_lora_mks0813_pixel_art",
        "repo_dir": "mks0813--z-image-turbo-pixel-art-lora",
        "repo_file": "z-image-turbo-pixel-art-lora.safetensors",
        "local_files": [
            "mks0813_pixel_art/mks0813_pixel_art.safetensors",
            "mks0813--z-image-turbo-pixel-lora/epoch-1.safetensors",
            "mks0813_pixel_art.safetensors",
        ],
        "trigger": "pxlstl",
        "scale": "1",
    },
    "SkyAsl--Pixel-artist-Z": {
        "profile": "nymphs_sprite_lora_skyasl_pixel_artist",
        "repo_dir": "SkyAsl--Pixel-artist-Z",
        "repo_file": "adapter_model.safetensors",
        "local_files": [
            "skyasl_pixel_artist/skyasl_pixel_artist.safetensors",
            "skyasl_pixel_artist.safetensors",
        ],
        "trigger": "a pixel art character",
        "scale": "1",
    },
    "tarn59--pixel_art_style_lora_z_image_turbo": {
        "profile": "nymphs_sprite_lora_tarn59_pixel_art",
        "repo_dir": "tarn59--pixel_art_style_lora_z_image_turbo",
        "repo_file": "pixel_art_style_z_image_turbo.safetensors",
        "local_files": [
            "tarn59_pixel_art/tarn59_pixel_art.safetensors",
            "tarn59_pixel_art.safetensors",
        ],
        "trigger": "Pixel art style.",
        "scale": "1",
    },
}

def emit(key: str, value: str) -> None:
    print(f"{key}={value or 'none'}")

def clean(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.:-]+", "_", value).strip("_") or "unknown"

def choice_name(path: Path) -> str:
    if path.parent != lora_root:
        return path.parent.name
    return path.name

def candidate_paths(candidate: dict[str, str]) -> list[Path]:
    paths = [lora_root / candidate["repo_dir"] / candidate["repo_file"]]
    paths.extend(lora_root / relative for relative in candidate.get("local_files", []))
    return paths

downloaded: list[str] = []
choices: list[str] = []
seen: set[Path] = set()
selected_path = ""
selected_id = ""
selected_trigger = ""
selected_scale = ""
downloaded_profiles: list[str] = []

for candidate_id, item in candidates.items():
    found = None
    for path in candidate_paths(item):
        if path.is_file():
            found = path
            break
    if found:
        resolved = found.resolve()
        downloaded.append(candidate_id)
        downloaded_profiles.append(item["profile"])
        choices.append(f"{item['profile']}|{candidate_id}|{resolved}")
        seen.add(resolved)
        if not selected_path:
            selected_id = item["profile"]
            selected_path = str(resolved)
            selected_trigger = item["trigger"]
            selected_scale = item["scale"]

if lora_root.is_dir():
    for path in sorted(path for path in lora_root.rglob("*.safetensors") if path.is_file()):
        resolved = path.resolve()
        if resolved in seen:
            continue
        display_name = choice_name(path)
        candidate_id = clean(display_name)
        downloaded.append(display_name)
        choices.append(f"{candidate_id}|{display_name}|{resolved}")
        if not selected_path:
            selected_id = candidate_id
            selected_path = str(resolved)

emit("downloaded_loras", ",".join(downloaded))
emit("downloaded_lora_profiles", ",".join(downloaded_profiles))
emit("lora_choices", ",".join(choices))
emit("selected_lora_candidate", selected_id)
emit("selected_lora_path", selected_path)
emit("selected_lora_trigger", selected_trigger)
emit("selected_lora_scale", selected_scale)
PY
)"

while IFS='=' read -r key value; do
  case "${key}" in
    downloaded_loras) downloaded_loras="${value}" ;;
    downloaded_lora_profiles) downloaded_lora_profiles="${value}" ;;
    lora_choices) lora_choices="${value}" ;;
    selected_lora_candidate) [[ "${value}" != "none" ]] && selected_lora_candidate="${value}" ;;
    selected_lora_path) [[ "${value}" != "none" ]] && selected_lora_path="${value}" ;;
    selected_lora_trigger) [[ "${value}" != "none" ]] && selected_lora_trigger="${value}" ;;
    selected_lora_scale) [[ "${value}" != "none" ]] && selected_lora_scale="${value}" ;;
  esac
done <<< "${lora_status}"

downloaded_fetch_profiles=()
missing_fetch_profiles=()
if [[ "${controlnet_ready}" == "true" ]]; then
  downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_CONTROLNET_PROFILE}")
else
  missing_fetch_profiles+=("${SPRITE_FOUNDRY_CONTROLNET_PROFILE}")
fi
case ",${downloaded_lora_profiles:-none}," in
  *,"${SPRITE_FOUNDRY_LORA_MKS0813_PROFILE}",*) downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_LORA_MKS0813_PROFILE}") ;;
  *) missing_fetch_profiles+=("${SPRITE_FOUNDRY_LORA_MKS0813_PROFILE}") ;;
esac
case ",${downloaded_lora_profiles:-none}," in
  *,"${SPRITE_FOUNDRY_LORA_SKYASL_PROFILE}",*) downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_LORA_SKYASL_PROFILE}") ;;
  *) missing_fetch_profiles+=("${SPRITE_FOUNDRY_LORA_SKYASL_PROFILE}") ;;
esac
case ",${downloaded_lora_profiles:-none}," in
  *,"${SPRITE_FOUNDRY_LORA_TARN59_PROFILE}",*) downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_LORA_TARN59_PROFILE}") ;;
  *) missing_fetch_profiles+=("${SPRITE_FOUNDRY_LORA_TARN59_PROFILE}") ;;
esac
if [[ "${map_depth_anything_ready}" == "true" ]]; then
  downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_MAP_DEPTH_ANYTHING_PROFILE}")
else
  missing_fetch_profiles+=("${SPRITE_FOUNDRY_MAP_DEPTH_ANYTHING_PROFILE}")
fi
if [[ "${map_midas_ready}" == "true" ]]; then
  downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_MAP_MIDAS_PROFILE}")
else
  missing_fetch_profiles+=("${SPRITE_FOUNDRY_MAP_MIDAS_PROFILE}")
fi
if [[ "${map_models_ready}" == "true" ]]; then
  downloaded_fetch_profiles+=("${SPRITE_FOUNDRY_MAP_ALL_PROFILE}")
else
  missing_fetch_profiles+=("${SPRITE_FOUNDRY_MAP_ALL_PROFILE}")
fi
if [[ ${#downloaded_fetch_profiles[@]} -gt 0 ]]; then
  weight_profiles_downloaded="$(IFS=,; printf '%s' "${downloaded_fetch_profiles[*]}")"
else
  weight_profiles_downloaded=none
fi
if [[ ${#missing_fetch_profiles[@]} -gt 0 ]]; then
  weight_profiles_missing="$(IFS=,; printf '%s' "${missing_fetch_profiles[*]}")"
else
  weight_profiles_missing=none
fi

if zimage_status_script="$(sprite_foundry_zimage_script zimage_status.sh 2>/dev/null)"; then
  zimage_status_output="$("${zimage_status_script}" 2>/dev/null || true)"
  while IFS='=' read -r key value; do
    case "${key}" in
      installed) zimage_installed="${value}" ;;
      running) zimage_running="${value}" ;;
      models_ready) zimage_models_ready="${value}" ;;
      health) zimage_health="${value}" ;;
      state) zimage_state="${value}" ;;
      detail) zimage_detail="${value}" ;;
      weight_profile_selected) zimage_weight_profile_selected="${value}" ;;
      weight_profile_ready) zimage_weight_profile_ready="${value}" ;;
      nunchaku_rank) zimage_nunchaku_rank="${value}" ;;
      nunchaku_precision) zimage_nunchaku_precision="${value}" ;;
      downloaded_models) zimage_downloaded_models="${value}" ;;
      downloaded_weights) zimage_downloaded_weights="${value}" ;;
      missing_weights) zimage_missing_weights="${value}" ;;
      hf_cache_dir) zimage_hf_cache_dir="${value}" ;;
      url) SPRITE_FOUNDRY_ZIMAGE_URL="${value}" ;;
    esac
  done <<< "${zimage_status_output}"
fi

if [[ "${controlnet_ready}" == "true" && "${zimage_models_ready}" == "true" && "${downloaded_loras}" != "none" ]]; then
  models_ready=true
fi

if [[ -f "${SPRITE_FOUNDRY_MARKER_FILE}" ]]; then
  installed=true
  runtime_present=true
  version="$(tr -d '\r\n' < "${SPRITE_FOUNDRY_MARKER_FILE}")"
  state="installed"
  health="ok"
  detail="${SPRITE_FOUNDRY_MODULE_NAME} is installed."
  if [[ "${controlnet_ready}" != "true" ]]; then
    state="model_download_needed"
    health="model-download-needed"
    detail="Nymphs Sprite ControlNet 2.1 needs downloading from this module's Details page."
  elif [[ "${zimage_installed}" != "true" ]]; then
    state="needs_attention"
    health="degraded"
    detail="Nymphs Sprite is installed, but the required Nymphs Image / Z-Image module is not installed."
  elif [[ "${zimage_models_ready}" != "true" ]]; then
    state="model_download_needed"
    health="model-download-needed"
    detail="Z-Image base/Nunchaku model files need downloading before Nymphs Sprite can generate."
  elif [[ "${downloaded_loras}" == "none" ]]; then
    state="model_download_needed"
    health="model-download-needed"
    detail="A Z-Image pixel-art LoRA is needed before Nymphs Sprite can generate."
  elif [[ "${zimage_running}" != "true" ]]; then
    state="installed"
    health="ok"
    detail="Nymphs Sprite assets are ready. Generate will start Nymphs Image / Z-Image automatically."
  fi
fi

if [[ -d "${SPRITE_FOUNDRY_OUTPUTS_ROOT}" || -d "${SPRITE_FOUNDRY_CONFIG_DIR}" || -d "${SPRITE_FOUNDRY_LOGS_DIR}" ]]; then
  data_present=true
fi

if [[ -f "${SPRITE_FOUNDRY_UI_PID_FILE}" ]]; then
  pid="$(tr -d '[:space:]' < "${SPRITE_FOUNDRY_UI_PID_FILE}" || true)"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1; then
    if sprite_foundry_probe_url "${SPRITE_FOUNDRY_UI_URL}/health" >/dev/null 2>&1; then
      running=true
      state="running"
      health="ok"
      if [[ "${zimage_running}" == "true" ]]; then
        detail="${SPRITE_FOUNDRY_MODULE_NAME} UI is running. Backend is ready at ${SPRITE_FOUNDRY_ZIMAGE_URL}."
      else
        detail="${SPRITE_FOUNDRY_MODULE_NAME} UI is running. Generate will start Nymphs Image / Z-Image automatically."
      fi
    else
      running=true
      state="running"
      health="unreachable"
      detail="${SPRITE_FOUNDRY_MODULE_NAME} UI process exists but health check failed."
    fi
  fi
fi

if [[ "${installed}" == "true" && ! -f "${SPRITE_FOUNDRY_INSTALL_DIR}/foundry/cli.py" ]]; then
  state="repair_needed"
  health="repair-needed"
  detail="${SPRITE_FOUNDRY_MODULE_NAME} install marker exists, but Foundry files are missing."
fi

printf 'id=%s\n' "${SPRITE_FOUNDRY_MODULE_ID}"
printf 'installed=%s\n' "${installed}"
printf 'runtime_present=%s\n' "${runtime_present}"
printf 'data_present=%s\n' "${data_present}"
printf 'version=%s\n' "${version}"
printf 'running=%s\n' "${running}"
printf 'state=%s\n' "${state}"
printf 'health=%s\n' "${health}"
printf 'detail=%s\n' "${detail}"
printf 'install_root=%s\n' "${SPRITE_FOUNDRY_INSTALL_DIR}"
printf 'outputs_root=%s\n' "${SPRITE_FOUNDRY_OUTPUTS_ROOT}"
printf 'ui_url=%s\n' "${SPRITE_FOUNDRY_UI_URL}"
printf 'zimage_url=%s\n' "${SPRITE_FOUNDRY_ZIMAGE_URL}"
printf 'controlnet_ready=%s\n' "${controlnet_ready}"
printf 'controlnet_profile=%s\n' "${SPRITE_FOUNDRY_CONTROLNET_PROFILE}"
printf 'controlnet_weight=%s/%s\n' "${SPRITE_FOUNDRY_CONTROLNET_REPO}" "${SPRITE_FOUNDRY_CONTROLNET_FILE}"
printf 'map_depth_anything_ready=%s\n' "${map_depth_anything_ready}"
printf 'map_depth_anything_profile=%s\n' "${SPRITE_FOUNDRY_MAP_DEPTH_ANYTHING_PROFILE}"
printf 'map_depth_anything_repo=%s\n' "${SPRITE_FOUNDRY_DEPTH_ANYTHING_REPO}"
printf 'map_midas_ready=%s\n' "${map_midas_ready}"
printf 'map_midas_profile=%s\n' "${SPRITE_FOUNDRY_MAP_MIDAS_PROFILE}"
printf 'map_midas_repo=%s\n' "${SPRITE_FOUNDRY_MIDAS_REPO}"
printf 'map_models_ready=%s\n' "${map_models_ready}"
printf 'map_models_profile=%s\n' "${SPRITE_FOUNDRY_MAP_ALL_PROFILE}"
printf 'models_ready=%s\n' "${models_ready}"
printf 'weight_profile_selected=%s\n' "${SPRITE_FOUNDRY_STARTER_PROFILE}"
printf 'weight_profiles_available=%s\n' "${weight_profiles_available}"
printf 'weight_profiles_downloaded=%s\n' "${weight_profiles_downloaded}"
printf 'weight_profiles_missing=%s\n' "${weight_profiles_missing}"
printf 'weight_profile_ready=%s\n' "${models_ready}"
printf 'downloaded_loras=%s\n' "${downloaded_loras}"
printf 'lora_choices=%s\n' "${lora_choices}"
printf 'selected_lora_candidate=%s\n' "${selected_lora_candidate}"
printf 'selected_lora_path=%s\n' "${selected_lora_path}"
printf 'selected_lora_trigger=%s\n' "${selected_lora_trigger}"
printf 'selected_lora_scale=%s\n' "${selected_lora_scale}"
printf 'lora_root=%s\n' "${SPRITE_FOUNDRY_LORA_ROOT}"
printf 'zimage_installed=%s\n' "${zimage_installed}"
printf 'zimage_running=%s\n' "${zimage_running}"
printf 'zimage_models_ready=%s\n' "${zimage_models_ready}"
printf 'zimage_health=%s\n' "${zimage_health}"
printf 'zimage_state=%s\n' "${zimage_state}"
printf 'zimage_detail=%s\n' "${zimage_detail}"
printf 'zimage_weight_profile_selected=%s\n' "${zimage_weight_profile_selected}"
printf 'zimage_weight_profile_ready=%s\n' "${zimage_weight_profile_ready}"
printf 'zimage_nunchaku_rank=%s\n' "${zimage_nunchaku_rank}"
printf 'zimage_nunchaku_precision=%s\n' "${zimage_nunchaku_precision}"
printf 'zimage_downloaded_models=%s\n' "${zimage_downloaded_models}"
printf 'zimage_downloaded_weights=%s\n' "${zimage_downloaded_weights}"
printf 'zimage_missing_weights=%s\n' "${zimage_missing_weights}"
printf 'zimage_hf_cache_dir=%s\n' "${zimage_hf_cache_dir}"
