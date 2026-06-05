#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

map_sprite_model_choice() {
  case "$1" in
    sprite_starter|sprite-starter|sprite_default|sprite-default|zimage_int4_r32|int4_r32)
      printf '%s\n' "svdq-int4_r32-z-image-turbo.safetensors"
      ;;
    zimage_int4_r128|int4_r128)
      printf '%s\n' "svdq-int4_r128-z-image-turbo.safetensors"
      ;;
    zimage_int4_r256|int4_r256)
      printf '%s\n' "svdq-int4_r256-z-image-turbo.safetensors"
      ;;
    zimage_fp4_r32|fp4_r32)
      printf '%s\n' "svdq-fp4_r32-z-image-turbo.safetensors"
      ;;
    zimage_fp4_r128|fp4_r128)
      printf '%s\n' "svdq-fp4_r128-z-image-turbo.safetensors"
      ;;
    *)
      printf '%s\n' "$1"
      ;;
  esac
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage:
  nymphs_sprite_fetch_models.sh --model sprite_starter
  nymphs_sprite_fetch_models.sh --model svdq-int4_r128-z-image-turbo.safetensors
  nymphs_sprite_fetch_models.sh --model complete_int4_package
  nymphs_sprite_fetch_models.sh --gpu-family rtx_20_30_40 --preset fast

This is a Sprite-facing bridge to the Nymphs Image / Z-Image model fetcher.
It writes to the same shared Hugging Face cache and Z-Image generation preset:
  $HOME/NymphsData/cache/huggingface
  $HOME/NymphsData/config/zimage/generation-preset.env

Sprite-friendly aliases:
  sprite_starter     -> Z-Image Turbo INT4 r32
  zimage_int4_r128   -> Z-Image Turbo INT4 r128
  zimage_int4_r256   -> Z-Image Turbo INT4 r256
  zimage_fp4_r32     -> Z-Image Turbo FP4 r32
  zimage_fp4_r128    -> Z-Image Turbo FP4 r128

All other arguments are passed through to zimage_fetch_models.sh.
EOF
  exit 0
fi

fetch_script="$(nymphs_sprite_zimage_script zimage_fetch_models.sh)" || {
  echo "ERROR: Nymphs Image / Z-Image fetcher is not installed." >&2
  echo "Expected ${HOME}/Z-Image/scripts/zimage_fetch_models.sh or a zimage module checkout." >&2
  exit 1
}

args=()
model_seen=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model|--weight|--download)
      if [[ $# -lt 2 ]]; then
        echo "$1 requires a model value." >&2
        exit 2
      fi
      args+=("--model" "$(map_sprite_model_choice "${2:-}")")
      model_seen=true
      shift 2
      ;;
    --model=*|--weight=*|--download=*)
      value="${1#*=}"
      args+=("--model" "$(map_sprite_model_choice "${value}")")
      model_seen=true
      shift
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ "${model_seen}" != "true" ]]; then
  args+=("--model" "svdq-int4_r32-z-image-turbo.safetensors")
fi

echo "sprite_model_fetch_delegate=zimage"
echo "sprite_model_fetch_script=${fetch_script}"
echo "shared_hf_cache_dir=${HOME}/NymphsData/cache/huggingface"
echo "shared_zimage_preset=${HOME}/NymphsData/config/zimage/generation-preset.env"
exec "${fetch_script}" "${args[@]}"
