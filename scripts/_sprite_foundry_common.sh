#!/usr/bin/env bash

SPRITE_FOUNDRY_MODULE_ID="nymphs-sprite"
SPRITE_FOUNDRY_MODULE_NAME="Nymphs Sprite"

NYMPHS_DATA_ROOT="${NYMPHS_DATA_ROOT:-${HOME}/NymphsData}"
SPRITE_FOUNDRY_INSTALL_DIR="${SPRITE_FOUNDRY_INSTALL_ROOT:-${SPRITE_FOUNDRY_INSTALL_DIR:-${HOME}/Nymphs-Sprite}}"
SPRITE_FOUNDRY_OUTPUTS_ROOT="${SPRITE_FOUNDRY_OUTPUTS_ROOT:-${NYMPHS_DATA_ROOT}/outputs/nymphs-sprite}"
SPRITE_FOUNDRY_CONFIG_DIR="${SPRITE_FOUNDRY_CONFIG_DIR:-${NYMPHS_DATA_ROOT}/config/nymphs-sprite}"
SPRITE_FOUNDRY_LOGS_DIR="${SPRITE_FOUNDRY_LOGS_DIR:-${NYMPHS_DATA_ROOT}/logs/nymphs-sprite}"
SPRITE_FOUNDRY_UI_HOST="${SPRITE_FOUNDRY_UI_HOST:-127.0.0.1}"
SPRITE_FOUNDRY_UI_PORT="${SPRITE_FOUNDRY_UI_PORT:-8098}"
SPRITE_FOUNDRY_UI_URL="${SPRITE_FOUNDRY_UI_URL:-http://${SPRITE_FOUNDRY_UI_HOST}:${SPRITE_FOUNDRY_UI_PORT}}"
SPRITE_FOUNDRY_MARKER_FILE="${SPRITE_FOUNDRY_INSTALL_DIR}/.nymph-module-version"
SPRITE_FOUNDRY_LOG_FILE="${SPRITE_FOUNDRY_LOGS_DIR}/nymphs-sprite.log"
SPRITE_FOUNDRY_UI_PID_FILE="${SPRITE_FOUNDRY_CONFIG_DIR}/ui-server.pid"
SPRITE_FOUNDRY_UI_LOG_FILE="${SPRITE_FOUNDRY_LOGS_DIR}/nymphs-sprite-ui.log"
SPRITE_FOUNDRY_ZIMAGE_URL="${SPRITE_FOUNDRY_ZIMAGE_URL:-http://127.0.0.1:8090}"
SPRITE_FOUNDRY_LORA_ROOT="${SPRITE_FOUNDRY_LORA_ROOT:-${ZIMAGE_LORA_ROOT:-${HOME}/LoRA/loras}}"
SPRITE_FOUNDRY_ZIMAGE_ROOT="${SPRITE_FOUNDRY_ZIMAGE_ROOT:-${ZIMAGE_INSTALL_ROOT:-${HOME}/Z-Image}}"
SPRITE_FOUNDRY_HF_CACHE_DIR="${SPRITE_FOUNDRY_HF_CACHE_DIR:-${NYMPHS_DATA_ROOT}/cache/huggingface}"
SPRITE_FOUNDRY_STARTER_PROFILE="nymphs_sprite_starter_stack"
SPRITE_FOUNDRY_CONTROLNET_PROFILE="nymphs_sprite_controlnet_2_1"
SPRITE_FOUNDRY_LORA_MKS0813_PROFILE="nymphs_sprite_lora_mks0813_pixel_art"
SPRITE_FOUNDRY_LORA_SKYASL_PROFILE="nymphs_sprite_lora_skyasl_pixel_artist"
SPRITE_FOUNDRY_LORA_TARN59_PROFILE="nymphs_sprite_lora_tarn59_pixel_art"
SPRITE_FOUNDRY_ALL_LORAS_PROFILE="nymphs_sprite_all_loras"
SPRITE_FOUNDRY_CONTROLNET_REPO="${SPRITE_FOUNDRY_CONTROLNET_REPO:-alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1}"
SPRITE_FOUNDRY_CONTROLNET_FILE="${SPRITE_FOUNDRY_CONTROLNET_FILE:-Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors}"

export NYMPHS_DATA_ROOT

sprite_foundry_ensure_dirs() {
  mkdir -p "${SPRITE_FOUNDRY_OUTPUTS_ROOT}" \
    "${SPRITE_FOUNDRY_CONFIG_DIR}" \
    "${SPRITE_FOUNDRY_LOGS_DIR}" \
    "${SPRITE_FOUNDRY_LORA_ROOT}"
}

sprite_foundry_version_from_manifest() {
  python3 - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    manifest = json.load(handle)

print(str(manifest.get("version", "unknown")).strip() or "unknown")
PY
}

sprite_foundry_touch_log() {
  sprite_foundry_ensure_dirs
  touch "${SPRITE_FOUNDRY_LOG_FILE}"
}

sprite_foundry_python_bin() {
  local zimage_root="${ZIMAGE_INSTALL_ROOT:-${HOME}/Z-Image}"
  if [[ -x "${zimage_root}/.venv-nunchaku/bin/python" ]]; then
    printf '%s\n' "${zimage_root}/.venv-nunchaku/bin/python"
    return 0
  fi
  command -v python3
}

sprite_foundry_zimage_root() {
  if [[ -f "${SPRITE_FOUNDRY_ZIMAGE_ROOT}/scripts/zimage_status.sh" ]]; then
    printf '%s\n' "${SPRITE_FOUNDRY_ZIMAGE_ROOT}"
    return 0
  fi

  local candidates=(
    "${HOME}/Z-Image"
    "${HOME}/NymphsModules/zimage"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -f "${candidate}/scripts/zimage_status.sh" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

sprite_foundry_zimage_script() {
  local script_name="$1"
  local zimage_root
  zimage_root="$(sprite_foundry_zimage_root)" || return 1
  if [[ -x "${zimage_root}/scripts/${script_name}" || -f "${zimage_root}/scripts/${script_name}" ]]; then
    printf '%s\n' "${zimage_root}/scripts/${script_name}"
    return 0
  fi
  return 1
}

sprite_foundry_root() {
  if [[ -f "${SPRITE_FOUNDRY_INSTALL_DIR}/foundry/cli.py" ]]; then
    printf '%s\n' "${SPRITE_FOUNDRY_INSTALL_DIR}"
    return 0
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local repo_dir
  repo_dir="$(cd "${script_dir}/.." && pwd)"
  if [[ -f "${repo_dir}/foundry/cli.py" ]]; then
    printf '%s\n' "${repo_dir}"
    return 0
  fi

  return 1
}

sprite_foundry_probe_url() {
  local url="$1"
  python3 - "${url}" <<'PY'
from __future__ import annotations

import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=1.5) as response:
    raise SystemExit(0 if 200 <= response.status < 300 else 1)
PY
}

sprite_foundry_start_zimage_backend() {
  if sprite_foundry_probe_url "${SPRITE_FOUNDRY_ZIMAGE_URL}/server_info" >/dev/null 2>&1; then
    printf 'Backend already running: %s\n' "${SPRITE_FOUNDRY_ZIMAGE_URL}"
    return 0
  fi

  local start_script
  if ! start_script="$(sprite_foundry_zimage_script zimage_start.sh 2>/dev/null)"; then
    printf 'ERROR: Nymphs Image / Z-Image is required but no zimage_start.sh was found.\n' >&2
    return 1
  fi

  printf 'Starting backend: Nymphs Image / Z-Image\n'
  "${start_script}"

  if sprite_foundry_probe_url "${SPRITE_FOUNDRY_ZIMAGE_URL}/server_info" >/dev/null 2>&1; then
    printf 'Backend ready: %s\n' "${SPRITE_FOUNDRY_ZIMAGE_URL}"
    return 0
  fi

  printf 'ERROR: Z-Image start finished, but %s/server_info did not answer.\n' "${SPRITE_FOUNDRY_ZIMAGE_URL}" >&2
  return 1
}

sprite_foundry_repo_cache_dir() {
  local repo_id="$1"
  local repo_path="${repo_id//\//--}"
  printf '%s/models--%s\n' "${SPRITE_FOUNDRY_HF_CACHE_DIR}" "${repo_path}"
}

sprite_foundry_cached_file_path() {
  local repo_id="$1"
  local filename="$2"
  local cache_dir
  cache_dir="$(sprite_foundry_repo_cache_dir "${repo_id}")"
  if [[ ! -d "${cache_dir}/snapshots" ]]; then
    return 1
  fi
  find -L "${cache_dir}/snapshots" -mindepth 2 -maxdepth 2 -type f -name "${filename}" -print -quit 2>/dev/null
}

sprite_foundry_controlnet_ready() {
  [[ -n "$(sprite_foundry_cached_file_path "${SPRITE_FOUNDRY_CONTROLNET_REPO}" "${SPRITE_FOUNDRY_CONTROLNET_FILE}" || true)" ]]
}
