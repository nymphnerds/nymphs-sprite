#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

selected_model="${SPRITE_FOUNDRY_STARTER_PROFILE}"
args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      selected_model="${2:-}"
      shift 2
      ;;
    --model=*)
      selected_model="${1#*=}"
      shift
      ;;
    --hf_token|--hf-token)
      export NYMPHS3D_HF_TOKEN="${2:-}"
      shift 2
      ;;
    --hf_token=*|--hf-token=*)
      export NYMPHS3D_HF_TOKEN="${1#*=}"
      shift
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

fetch_script="$(sprite_foundry_zimage_script zimage_fetch_models.sh 2>/dev/null || true)"
python_bin="$(sprite_foundry_python_bin)"

format_bytes() {
  local bytes="${1:-0}"
  python3 - "${bytes}" <<'PY'
import sys

try:
    value = float(sys.argv[1])
except Exception:
    value = 0.0

for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
    if value < 1024 or unit == "TiB":
        print(f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B")
        break
    value /= 1024
PY
}

cache_size_bytes() {
  local path="$1"
  if [[ ! -d "${path}" ]]; then
    echo 0
    return
  fi
  du -sb "${path}" 2>/dev/null | awk '{print $1}'
}

hf_repo_cache_dir() {
  local repo_id="$1"
  printf '%s/models--%s\n' "${SPRITE_FOUNDRY_HF_CACHE_DIR}" "${repo_id//\//--}"
}

hf_repo_blob_bytes() {
  local repo_id="$1"
  local repo_dir
  repo_dir="$(hf_repo_cache_dir "${repo_id}")"
  cache_size_bytes "${repo_dir}/blobs"
}

hf_repo_active_download_count() {
  local repo_id="$1"
  local repo_dir
  repo_dir="$(hf_repo_cache_dir "${repo_id}")"
  if [[ ! -d "${repo_dir}" ]]; then
    echo 0
    return
  fi
  find "${repo_dir}" -type f \( -name '*.incomplete' -o -name '*.lock' \) 2>/dev/null | wc -l | tr -d ' '
}

print_hf_download_progress() {
  local label="$1"
  local repo_id="$2"
  local repo_bytes
  local active_count
  repo_bytes="$(hf_repo_blob_bytes "${repo_id}")"
  active_count="$(hf_repo_active_download_count "${repo_id}")"
  echo "MODEL FETCH STATUS: step=${label} repo=${repo_id} status=downloading this_repo_cache=$(format_bytes "${repo_bytes}") active_download_files=${active_count}"
}

run_with_hf_download_progress() {
  local label="$1"
  local repo_id="$2"
  shift 2

  local interval="${SPRITE_FOUNDRY_FETCH_PROGRESS_INTERVAL:-5}"
  local marker
  local pid
  local status
  if [[ ! "${interval}" =~ ^[0-9]+$ || "${interval}" -lt 1 ]]; then
    interval=5
  fi

  marker="$(mktemp "${TMPDIR:-/tmp}/nymphs-sprite-fetch.XXXXXX.status")"
  rm -f "${marker}"

  echo "MODEL FETCH STARTED: step=${label} repo=${repo_id}"
  print_hf_download_progress "${label}" "${repo_id}"
  (
    set +e
    "$@"
    printf '%s\n' "$?" > "${marker}"
  ) &
  pid=$!

  while [[ ! -f "${marker}" ]]; do
    sleep "${interval}"
    [[ -f "${marker}" ]] && break
    print_hf_download_progress "${label}" "${repo_id}"
  done

  wait "${pid}" || true
  status="$(cat "${marker}" 2>/dev/null || echo 1)"
  rm -f "${marker}"

  if [[ "${status}" -eq 0 ]]; then
    print_hf_download_progress "${label}" "${repo_id}"
    echo "MODEL FETCH COMPLETE: step=${label} repo=${repo_id}"
  else
    echo "MODEL FETCH FAILED: step=${label} repo=${repo_id} exit_status=${status}"
  fi
  return "${status}"
}

fetch_zimage_profile() {
  local model="$1"
  if [[ -z "${fetch_script}" ]]; then
    echo "ERROR: Nymphs Sprite needs Nymphs Image installed to fetch shared Z-Image backend weights." >&2
    echo "expected=${HOME}/Z-Image/scripts/zimage_fetch_models.sh" >&2
    exit 1
  fi
  echo "delegate=nymphs-image"
  echo "model=${model}"
  echo "fetch_script=${fetch_script}"
  "${fetch_script}" --model "${model}" "${args[@]}"
}

fetch_lora() {
  local profile="$1"
  local repo_id="$2"
  local repo_file="$3"
  local library_dir="${repo_id//\//--}"

  sprite_foundry_ensure_dirs
  echo "model_fetch_plan=Nymphs Sprite LoRA ${profile}"
  download_lora() {
    "${python_bin}" - "${repo_id}" "${repo_file}" "${SPRITE_FOUNDRY_HF_CACHE_DIR}" "${SPRITE_FOUNDRY_LORA_ROOT}" "${library_dir}" <<'PY'
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download
except Exception as exc:
    raise SystemExit(f"ERROR: huggingface_hub is required to fetch Nymphs Sprite LoRAs: {exc}")

repo_id, repo_file, cache_dir, lora_root, library_dir = sys.argv[1:6]
token = os.getenv("NYMPHS3D_HF_TOKEN") or os.getenv("HF_TOKEN") or None
downloaded = Path(hf_hub_download(repo_id=repo_id, filename=repo_file, cache_dir=cache_dir, token=token))
target_dir = Path(lora_root).expanduser() / library_dir
target_dir.mkdir(parents=True, exist_ok=True)
target = target_dir / repo_file
if downloaded.resolve() != target.resolve():
    shutil.copy2(downloaded, target)
print(f"MODEL FETCH COMPLETE: lora_path={target}", flush=True)
PY
  }
  run_with_hf_download_progress "Nymphs Sprite LoRA" "${repo_id}" download_lora
}

fetch_mks0813() {
  fetch_lora \
    "${SPRITE_FOUNDRY_LORA_MKS0813_PROFILE}" \
    "mks0813/z-image-turbo-pixel-art-lora" \
    "z-image-turbo-pixel-art-lora.safetensors"
}

fetch_skyasl() {
  fetch_lora \
    "${SPRITE_FOUNDRY_LORA_SKYASL_PROFILE}" \
    "SkyAsl/Pixel-artist-Z" \
    "adapter_model.safetensors"
}

fetch_tarn59() {
  fetch_lora \
    "${SPRITE_FOUNDRY_LORA_TARN59_PROFILE}" \
    "tarn59/pixel_art_style_lora_z_image_turbo" \
    "pixel_art_style_z_image_turbo.safetensors"
}

case "${selected_model}" in
  "${SPRITE_FOUNDRY_STARTER_PROFILE}")
    echo "Nymphs Sprite starter stack fetch"
    fetch_zimage_profile int4_r32
    fetch_zimage_profile zimage_controlnet_2_1
    fetch_mks0813
    ;;
  "${SPRITE_FOUNDRY_ALL_LORAS_PROFILE}")
    fetch_mks0813
    fetch_skyasl
    fetch_tarn59
    ;;
  "${SPRITE_FOUNDRY_CONTROLNET_PROFILE}")
    echo "Nymphs Sprite ControlNet fetch"
    fetch_zimage_profile zimage_controlnet_2_1
    ;;
  "${SPRITE_FOUNDRY_LORA_MKS0813_PROFILE}")
    fetch_mks0813
    ;;
  "${SPRITE_FOUNDRY_LORA_SKYASL_PROFILE}")
    fetch_skyasl
    ;;
  "${SPRITE_FOUNDRY_LORA_TARN59_PROFILE}")
    fetch_tarn59
    ;;
  *)
    echo "Unsupported Nymphs Sprite fetch selection: ${selected_model:-none}" >&2
    echo "Expected one of the nymphs_sprite_* fetch profiles from nymph.json." >&2
    exit 2
    ;;
esac

cat <<EOF
MODEL FETCH COMPLETE
selected=${selected_model}
shared_lora_root=${SPRITE_FOUNDRY_LORA_ROOT}
shared_hf_cache=${SPRITE_FOUNDRY_HF_CACHE_DIR}
EOF
