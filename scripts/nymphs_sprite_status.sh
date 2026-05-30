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
selected_lora_trigger=""
selected_lora_scale=""

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
  selected_lora_path="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_PATH=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_trigger="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_TRIGGER=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_scale="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_SCALE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
fi

if [[ "${installed}" == "true" && "${runtime_present}" == "false" ]]; then
  state=repair_needed
  health=repair-needed
  detail="${NYMPHS_SPRITE_MODULE_NAME} is installed, but module files are missing."
elif [[ "${installed}" == "true" ]]; then
  state=installed
  health=ok
  detail="${NYMPHS_SPRITE_MODULE_NAME} is installed. Open the module UI, start Nymphs Image, then generate through Z-Image Turbo with a sprite LoRA."
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
controlnet_dir=${NYMPHS_SPRITE_CONTROLNET_DIR}
depth_models_dir=${NYMPHS_SPRITE_DEPTH_MODELS_DIR}
workflows_dir=${NYMPHS_SPRITE_WORKFLOWS_DIR}
profiles_dir=${NYMPHS_SPRITE_PROFILES_DIR}
docs_dir=${NYMPHS_SPRITE_DOCS_DIR}
ui_dir=${NYMPHS_SPRITE_UI_DIR}
manager_ui=${NYMPHS_SPRITE_UI_DIR}/manager.html
lora_root=${NYMPHS_SPRITE_LORA_ROOT}
lora_dir=${NYMPHS_SPRITE_LORA_DIR}
selected_lora_path=${selected_lora_path}
selected_lora_trigger=${selected_lora_trigger}
selected_lora_scale=${selected_lora_scale}
lora_preset_file=${NYMPHS_SPRITE_LORA_PRESET_FILE}
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
