#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

foundry_root="$(nymphs_sprite_foundry_root || true)"
if [[ -z "${foundry_root}" ]]; then
  cat <<STATUS
foundry_available=false
foundry_root=${NYMPHS_SPRITE_FOUNDRY_ROOT}
detail=Sprite Foundry fork was not found. Set NYMPHS_SPRITE_FOUNDRY_ROOT to a checkout containing foundry/cli.py.
STATUS
  exit 1
fi

db_path="${foundry_root}/foundry.db"

echo "foundry_available=true"
echo "foundry_root=${foundry_root}"
echo "foundry_db=${db_path}"
if [[ -f "${db_path}" ]]; then
  echo "foundry_db_present=true"
else
  echo "foundry_db_present=false"
fi

cd "${foundry_root}"
echo
echo "=== verify ==="
if bash "${foundry_root}/verify.sh"; then
  echo "foundry_verify=ok"
else
  echo "foundry_verify=failed"
  exit 1
fi

echo
echo "=== status ==="
if [[ -f "${db_path}" ]]; then
  python3 -m foundry.cli status
else
  echo "Foundry database has not been initialized yet."
  echo "Next: python3 -m foundry.cli init"
fi
