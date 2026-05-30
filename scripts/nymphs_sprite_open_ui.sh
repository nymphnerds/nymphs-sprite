#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

ui_path="${NYMPHS_SPRITE_UI_DIR}/manager.html"
if [[ ! -f "${ui_path}" ]]; then
  echo "ERROR: Nymphs Sprite Manager UI is missing. Run Install, Update, or Repair." >&2
  exit 1
fi

echo "module_ui=${ui_path}"
echo "Nymphs Sprite UI is installed."
