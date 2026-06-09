#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

root="$(sprite_foundry_root)"
python_bin="$(sprite_foundry_python_bin)"

cd "${root}"
exec "${python_bin}" -m foundry.cli status --verbose
