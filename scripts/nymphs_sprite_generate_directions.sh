#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

python_bin="$(nymphs_sprite_python_bin)"

extra_args=()
if [[ -f "${NYMPHS_SPRITE_LORA_PRESET_FILE}" ]]; then
  selected_lora_path="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_PATH=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_trigger="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_TRIGGER=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_scale="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_SCALE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  if [[ -n "${selected_lora_path}" ]]; then
    extra_args+=(--lora-path "${selected_lora_path}")
  fi
  if [[ -n "${selected_lora_trigger}" ]]; then
    extra_args+=(--lora-trigger "${selected_lora_trigger}")
  fi
  if [[ -n "${selected_lora_scale}" ]]; then
    extra_args+=(--lora-scale "${selected_lora_scale}")
  fi
fi

exec "${python_bin}" "${SCRIPT_DIR}/nymphs_sprite_generate_directions.py" \
  --zimage-url "${NYMPHS_SPRITE_ZIMAGE_URL}" \
  "${extra_args[@]}" \
  "$@"
