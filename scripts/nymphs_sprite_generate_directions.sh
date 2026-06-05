#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

python_bin="$(nymphs_sprite_python_bin)"

extra_args=()
pass_args=()
declare -A encoded_parts=()

decode_base64url() {
  "${python_bin}" - "$1" <<'PY'
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
    subject-prompt-b64-*|negative-prompt-b64-*|lora-path-b64-*|lora-trigger-b64-*|source-images-b64-*)
      encoded_parts["${key}"]="${value}"
      return 0
      ;;
  esac
  return 1
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
        pass_args+=("$1")
        shift
      fi
      ;;
    --subject-prompt-b64-*|--negative-prompt-b64-*|--lora-path-b64-*|--lora-trigger-b64-*|--source-images-b64-*)
      key="${1#--}"
      value="${2:-}"
      collect_encoded_arg "${key}" "${value}"
      shift 2
      ;;
    *)
      pass_args+=("$1")
      shift
      ;;
  esac
done

append_decoded_arg() {
  local prefix="$1"
  local target="$2"
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
    pass_args+=("--${target}" "$(decode_base64url "${encoded}")")
  fi
}

append_decoded_arg "subject-prompt" "subject-prompt"
append_decoded_arg "negative-prompt" "negative-prompt"
append_decoded_arg "lora-path" "lora-path"
append_decoded_arg "lora-trigger" "lora-trigger"
append_decoded_arg "source-images" "source-images"

zimage_probe() {
  "${python_bin}" - "${NYMPHS_SPRITE_ZIMAGE_URL%/}/server_info" <<'PY' >/dev/null 2>&1
from __future__ import annotations

import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=3):
    pass
PY
}

if ! zimage_probe; then
  if [[ "${NYMPHS_SPRITE_AUTO_START_ZIMAGE:-1}" == "1" ]]; then
    echo "Z-Image is not responding at ${NYMPHS_SPRITE_ZIMAGE_URL}; starting Nymphs Image..."
    "${SCRIPT_DIR}/nymphs_sprite_start_zimage.sh"
  fi
fi

if ! zimage_probe; then
  echo "ERROR: Z-Image is not responding at ${NYMPHS_SPRITE_ZIMAGE_URL}. Start Nymphs Image from Manager, then try again." >&2
  exit 1
fi

if [[ -f "${NYMPHS_SPRITE_LORA_PRESET_FILE}" ]]; then
  selected_lora_candidate="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_CANDIDATE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_path="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_PATH=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_trigger="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_TRIGGER=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  selected_lora_scale="$(sed -n 's/^NYMPHS_SPRITE_SELECTED_LORA_SCALE=//p' "${NYMPHS_SPRITE_LORA_PRESET_FILE}" | tail -n 1)"
  profile_file="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/zimage_turbo_lora_candidates.json"
  if [[ ! -f "${profile_file}" ]]; then
    profile_file="${NYMPHS_SPRITE_PROFILES_DIR}/zimage_turbo_lora_candidates.json"
  fi
  resolved_lora_path="$("${python_bin}" - "${profile_file}" "${NYMPHS_SPRITE_LORA_DIR}" "${selected_lora_candidate}" "${selected_lora_path}" <<'PY'
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
  [[ -n "${resolved_lora_path}" ]] && selected_lora_path="${resolved_lora_path}"
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
  --outputs-root "${NYMPHS_SPRITE_OUTPUTS_ROOT}" \
  "${pass_args[@]}" \
  "${extra_args[@]}"
