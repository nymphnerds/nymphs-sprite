#!/usr/bin/env bash

NYMPHS_SPRITE_MODULE_ID="nymphs-sprite"
NYMPHS_SPRITE_MODULE_NAME="Nymphs Sprite"

NYMPHS_SPRITE_INSTALL_DIR="${NYMPHS_SPRITE_INSTALL_ROOT:-${NYMPHS_SPRITE_INSTALL_DIR:-${HOME}/Nymphs-Sprite}}"
NYMPHS_SPRITE_OUTPUTS_ROOT="${NYMPHS_SPRITE_OUTPUTS_ROOT:-${HOME}/NymphsData/outputs/nymphs-sprite}"
NYMPHS_SPRITE_CONFIG_DIR="${NYMPHS_SPRITE_CONFIG_DIR:-${HOME}/NymphsData/config/nymphs-sprite}"
NYMPHS_SPRITE_LOGS_DIR="${NYMPHS_SPRITE_LOGS_DIR:-${HOME}/NymphsData/logs/nymphs-sprite}"
NYMPHS_SPRITE_MODELS_ROOT="${NYMPHS_SPRITE_MODELS_ROOT:-${HOME}/NymphsData/models/nymphs-sprite}"
NYMPHS_SPRITE_CONTROLNET_DIR="${NYMPHS_SPRITE_CONTROLNET_DIR:-${NYMPHS_SPRITE_MODELS_ROOT}/controlnet}"
NYMPHS_SPRITE_DEPTH_MODELS_DIR="${NYMPHS_SPRITE_DEPTH_MODELS_DIR:-${NYMPHS_SPRITE_MODELS_ROOT}/depth}"
NYMPHS_SPRITE_WORKFLOWS_DIR="${NYMPHS_SPRITE_INSTALL_DIR}/comfyui_workflows"
NYMPHS_SPRITE_PROFILES_DIR="${NYMPHS_SPRITE_INSTALL_DIR}/profiles"
NYMPHS_SPRITE_DOCS_DIR="${NYMPHS_SPRITE_INSTALL_DIR}/docs"
NYMPHS_SPRITE_UI_DIR="${NYMPHS_SPRITE_INSTALL_DIR}/ui"
NYMPHS_SPRITE_MARKER_FILE="${NYMPHS_SPRITE_INSTALL_DIR}/.nymph-module-version"
NYMPHS_SPRITE_LOG_FILE="${NYMPHS_SPRITE_LOGS_DIR}/nymphs-sprite.log"
NYMPHS_SPRITE_LORA_ROOT="${NYMPHS_SPRITE_LORA_ROOT:-${ZIMAGE_LORA_ROOT:-${HOME}/LoRA/loras}}"
NYMPHS_SPRITE_ZIMAGE_URL="${NYMPHS_SPRITE_ZIMAGE_URL:-http://127.0.0.1:8090}"
NYMPHS_SPRITE_LORA_DIR="${NYMPHS_SPRITE_LORA_DIR:-${NYMPHS_SPRITE_LORA_ROOT}/nymphs-sprite}"
NYMPHS_SPRITE_LORA_PRESET_FILE="${NYMPHS_SPRITE_CONFIG_DIR}/selected_lora.env"

nymphs_sprite_ensure_dirs() {
  mkdir -p "${NYMPHS_SPRITE_OUTPUTS_ROOT}" \
    "${NYMPHS_SPRITE_CONFIG_DIR}" \
    "${NYMPHS_SPRITE_LOGS_DIR}" \
    "${NYMPHS_SPRITE_CONTROLNET_DIR}" \
    "${NYMPHS_SPRITE_DEPTH_MODELS_DIR}" \
    "${NYMPHS_SPRITE_LORA_DIR}"
}

nymphs_sprite_python_bin() {
  local zimage_root="${ZIMAGE_INSTALL_ROOT:-${HOME}/Z-Image}"
  if [[ -x "${zimage_root}/.venv-nunchaku/bin/python" ]]; then
    printf '%s\n' "${zimage_root}/.venv-nunchaku/bin/python"
    return 0
  fi
  command -v python3
}

nymphs_sprite_version_from_manifest() {
  python3 - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    manifest = json.load(handle)

print(str(manifest.get("version", "unknown")).strip() or "unknown")
PY
}

nymphs_sprite_touch_log() {
  nymphs_sprite_ensure_dirs
  touch "${NYMPHS_SPRITE_LOG_FILE}"
}
