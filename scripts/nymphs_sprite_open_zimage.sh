#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

zimage_root="${ZIMAGE_INSTALL_ROOT:-${HOME}/Z-Image}"
zimage_script="${zimage_root}/scripts/zimage_nymph_ui.sh"

if [[ ! -x "${zimage_script}" ]]; then
  fallback="${HOME}/NymphsModules/zimage/scripts/zimage_nymph_ui.sh"
  if [[ -x "${fallback}" ]]; then
    zimage_script="${fallback}"
  fi
fi

if [[ ! -x "${zimage_script}" ]]; then
  echo "ERROR: Nymphs Image / Z-Image start script was not found." >&2
  echo "expected=${zimage_root}/scripts/zimage_nymph_ui.sh" >&2
  exit 1
fi

echo "Starting Nymphs Image for the sprite flow..."
"${zimage_script}" "$@"
echo "sprite_backend=${NYMPHS_SPRITE_ZIMAGE_URL}"
