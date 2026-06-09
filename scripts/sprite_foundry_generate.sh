#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

generation_path="nymphscore"
config="pipeline/chars/goblin_scout.json"
sprite_size="96"
palette_colors="0"
steps="9"
seed=""
width=""
height=""
lora_path=""
lora_trigger=""
lora_scale=""
nunchaku_rank=""
nunchaku_precision=""
body_class=""
depth_refs=""
edge_refs=""
subject_id=""
subject_prompt_parts=()
negative_prompt_parts=()
lora_path_parts=()
lora_trigger_parts=()
extra_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --generation-path)
      generation_path="$2"
      shift 2
      ;;
    --config)
      config="$2"
      shift 2
      ;;
    --sprite-size)
      sprite_size="$2"
      shift 2
      ;;
    --palette-colors)
      palette_colors="$2"
      shift 2
      ;;
    --steps)
      steps="$2"
      shift 2
      ;;
    --seed)
      seed="$2"
      shift 2
      ;;
    --width)
      width="$2"
      shift 2
      ;;
    --height)
      height="$2"
      shift 2
      ;;
    --lora-path)
      lora_path="$2"
      shift 2
      ;;
    --lora-path-b64-*)
      lora_path_parts+=("${1#--lora-path-b64-}=$2")
      shift 2
      ;;
    --lora-trigger)
      lora_trigger="$2"
      shift 2
      ;;
    --lora-trigger-b64-*)
      lora_trigger_parts+=("${1#--lora-trigger-b64-}=$2")
      shift 2
      ;;
    --lora-scale)
      lora_scale="$2"
      shift 2
      ;;
    --nunchaku-rank)
      nunchaku_rank="$2"
      shift 2
      ;;
    --nunchaku-precision)
      nunchaku_precision="$2"
      shift 2
      ;;
    --subject-id)
      subject_id="$2"
      shift 2
      ;;
    --subject-prompt-b64-*)
      subject_prompt_parts+=("${1#--subject-prompt-b64-}=$2")
      shift 2
      ;;
    --negative-prompt-b64-*)
      negative_prompt_parts+=("${1#--negative-prompt-b64-}=$2")
      shift 2
      ;;
    --body-class)
      body_class="$2"
      shift 2
      ;;
    --depth-refs)
      depth_refs="$2"
      shift 2
      ;;
    --edge-refs)
      edge_refs="$2"
      shift 2
      ;;
    *)
      extra_args+=("$1")
      shift
      ;;
  esac
done

decode_b64_chunks() {
  python3 - "$@" <<'PY'
from __future__ import annotations

import base64
import sys

parts = []
for item in sys.argv[1:]:
    key, _, value = item.partition("=")
    try:
        index = int(key)
    except ValueError:
        index = 0
    parts.append((index, value))
raw = "".join(value for _, value in sorted(parts))
if not raw:
    raise SystemExit(0)
padding = "=" * (-len(raw) % 4)
print(base64.urlsafe_b64decode((raw + padding).encode("ascii")).decode("utf-8"))
PY
}

root="$(sprite_foundry_root)"
python_bin="$(sprite_foundry_python_bin)"
sprite_foundry_ensure_dirs

cd "${root}"
subject_prompt="$(decode_b64_chunks "${subject_prompt_parts[@]}")"
negative_prompt="$(decode_b64_chunks "${negative_prompt_parts[@]}")"
decoded_lora_path="$(decode_b64_chunks "${lora_path_parts[@]}")"
if [[ -n "${decoded_lora_path}" ]]; then
  lora_path="${decoded_lora_path}"
fi
decoded_lora_trigger="$(decode_b64_chunks "${lora_trigger_parts[@]}")"
if [[ -n "${decoded_lora_trigger}" ]]; then
  lora_trigger="${decoded_lora_trigger}"
fi

if [[ "${generation_path}" == "nymphscore" && -n "${subject_prompt}" ]]; then
  safe_subject_id="$(python3 - "${subject_id:-sprite_subject}" <<'PY'
from __future__ import annotations

import re
import sys

value = re.sub(r"[^A-Za-z0-9_]+", "_", (sys.argv[1] or "sprite_subject").strip()).strip("_")
print((value or "sprite_subject")[:80])
PY
)"
  ui_config_dir="${SPRITE_FOUNDRY_CONFIG_DIR}/runs"
  mkdir -p "${ui_config_dir}"
  config="${ui_config_dir}/${safe_subject_id}.json"
  SF_CONFIG_PATH="${config}" \
  SF_SUBJECT_ID="${safe_subject_id}" \
  SF_SUBJECT_PROMPT="${subject_prompt}" \
  SF_NEGATIVE_PROMPT="${negative_prompt}" \
  SF_SEED="${seed:-0}" \
  python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

path = Path(os.environ["SF_CONFIG_PATH"])
subject_id = os.environ["SF_SUBJECT_ID"]
seed_text = os.environ.get("SF_SEED") or "0"
try:
    seed = int(seed_text)
except ValueError:
    seed = 0
payload = {
    "subject_id": subject_id,
    "display_name": subject_id.replace("_", " ").title(),
    "role": "sprite",
    "consumer": "nymphscore",
    "subject_prompt": os.environ["SF_SUBJECT_PROMPT"],
    "negative_prompt": os.environ.get("SF_NEGATIVE_PROMPT", ""),
    "seed": seed,
}
path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
fi

case "${generation_path}" in
  nymphscore)
    sprite_foundry_start_zimage_backend
    cmd=("${python_bin}" -m foundry.cli generate-nymphscore --config "${config}" --nymphscore-url "${SPRITE_FOUNDRY_ZIMAGE_URL}" --sprite-size "${sprite_size}" --steps "${steps}")
    if [[ -n "${seed}" ]]; then
      cmd+=(--seed "${seed}")
    fi
    if [[ -n "${palette_colors}" ]]; then
      cmd+=(--palette-colors "${palette_colors}")
    fi
    if [[ -n "${width}" ]]; then
      cmd+=(--width "${width}")
    fi
    if [[ -n "${height}" ]]; then
      cmd+=(--height "${height}")
    fi
    if [[ -n "${lora_path}" ]]; then
      cmd+=(--lora-path "${lora_path}")
    fi
    if [[ -n "${lora_trigger}" ]]; then
      cmd+=(--lora-trigger "${lora_trigger}")
    fi
    if [[ -n "${lora_scale}" ]]; then
      cmd+=(--lora-scale "${lora_scale}")
    fi
    if [[ -n "${nunchaku_rank}" ]]; then
      cmd+=(--nunchaku-rank "${nunchaku_rank}")
    fi
    if [[ -n "${nunchaku_precision}" ]]; then
      cmd+=(--nunchaku-precision "${nunchaku_precision}")
    fi
    ;;
  stack_a_v2)
    cmd=("${python_bin}" -m foundry.cli generate-stack-a-v2 --config "${config}")
    ;;
  morph)
    cmd=("${python_bin}" -m foundry.cli generate-morph --config "${config}")
    if [[ -n "${body_class}" ]]; then
      cmd+=(--body-class "${body_class}")
    fi
    if [[ -n "${depth_refs}" ]]; then
      cmd+=(--depth-refs "${depth_refs}")
    fi
    if [[ -n "${edge_refs}" ]]; then
      cmd+=(--edge-refs "${edge_refs}")
    fi
    ;;
  turnaround)
    cmd=("${python_bin}" -m foundry.cli generate-turnaround --config "${config}")
    ;;
  *)
    echo "Unknown Foundry generation path: ${generation_path}" >&2
    echo "Expected one of: nymphscore, stack_a_v2, morph, turnaround" >&2
    exit 2
    ;;
esac

cmd+=("${extra_args[@]}")
{
  printf 'run_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'generation_path=%s\n' "${generation_path}"
  printf 'config=%s\n' "${config}"
} >> "${SPRITE_FOUNDRY_LOG_FILE}"

exec "${cmd[@]}"
