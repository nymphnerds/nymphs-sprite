#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

asset="complete_sprite"
hf_token=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --asset|--model|--download)
      if [[ $# -lt 2 ]]; then
        echo "$1 requires an asset id." >&2
        exit 2
      fi
      asset="${2:-}"
      shift 2
      ;;
    --asset=*|--model=*|--download=*)
      asset="${1#*=}"
      shift
      ;;
    --candidate|--lora)
      if [[ $# -lt 2 ]]; then
        echo "$1 requires a LoRA candidate id." >&2
        exit 2
      fi
      asset="${2:-}"
      shift 2
      ;;
    --candidate=*|--lora=*)
      asset="${1#*=}"
      shift
      ;;
    --hf_token|--hf-token)
      if [[ $# -lt 2 || "${2:-}" == --* ]]; then
        hf_token=""
        shift 1
      else
        hf_token="${2:-}"
        shift 2
      fi
      ;;
    --hf_token=*|--hf-token=*)
      hf_token="${1#*=}"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  nymphs_sprite_fetch_assets.sh --asset complete_sprite
  nymphs_sprite_fetch_assets.sh --asset mks0813_pixel_art
  nymphs_sprite_fetch_assets.sh --asset controlnet_union
  nymphs_sprite_fetch_assets.sh --asset depth_anything_small
  nymphs_sprite_fetch_assets.sh --asset all_sprite_assets

Fetches module-owned sprite assets. Base Z-Image, Nunchaku, and Qwen weights
remain owned by the Nymphs Image / Z-Image module.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unsupported argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -n "${hf_token}" ]]; then
  export NYMPHS3D_HF_TOKEN="${hf_token}"
  export HF_TOKEN="${hf_token}"
  export HUGGING_FACE_HUB_TOKEN="${hf_token}"
fi

case "${asset}" in
  mks0813_pixel_art|tarn59_pixel_art)
    echo "asset_fetch_plan=LoRA:${asset}"
    exec "${SCRIPT_DIR}/nymphs_sprite_fetch_lora.sh" --candidate "${asset}"
    ;;
  controlnet_union)
    echo "asset_fetch_plan=ControlNet:Z-Image-Turbo-Fun-Controlnet-Union"
    exec "${SCRIPT_DIR}/nymphs_sprite_fetch_controlnet.sh"
    ;;
  depth_anything_small)
    echo "asset_fetch_plan=Depth:Depth-Anything-V2-Small-hf"
    exec "${SCRIPT_DIR}/nymphs_sprite_fetch_depth_anything.sh" --small
    ;;
  complete_sprite|all_sprite_assets)
    echo "asset_fetch_plan=LoRA:mks0813_pixel_art,LoRA:tarn59_pixel_art,ControlNet:union,Depth:small"
    "${SCRIPT_DIR}/nymphs_sprite_fetch_lora.sh" --candidate tarn59_pixel_art
    "${SCRIPT_DIR}/nymphs_sprite_fetch_lora.sh" --candidate mks0813_pixel_art
    "${SCRIPT_DIR}/nymphs_sprite_fetch_controlnet.sh"
    "${SCRIPT_DIR}/nymphs_sprite_fetch_depth_anything.sh" --small
    echo "asset_fetch_complete=complete_sprite"
    echo "selected_lora=mks0813_pixel_art"
    ;;
  *)
    echo "ERROR: unknown sprite asset id: ${asset}" >&2
    exit 2
    ;;
esac
