#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

sprite_foundry_ensure_dirs
printf 'outputs_root=%s\n' "${SPRITE_FOUNDRY_OUTPUTS_ROOT}"
printf 'directory=%s\n' "${SPRITE_FOUNDRY_OUTPUTS_ROOT}"
