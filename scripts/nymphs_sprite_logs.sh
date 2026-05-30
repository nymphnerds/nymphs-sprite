#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

nymphs_sprite_touch_log
echo "last_log=${NYMPHS_SPRITE_LOG_FILE}"
echo "${NYMPHS_SPRITE_LOG_FILE}"

