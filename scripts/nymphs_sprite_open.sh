#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

if [[ -d "${NYMPHS_SPRITE_DOCS_DIR}" ]]; then
  echo "${NYMPHS_SPRITE_DOCS_DIR}"
else
  echo "${NYMPHS_SPRITE_INSTALL_DIR}"
fi

