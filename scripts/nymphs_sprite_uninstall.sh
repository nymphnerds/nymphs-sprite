#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

dry_run=false
confirmed=false
purge=false
data_only=false

for arg in "$@"; do
  case "${arg}" in
    --dry-run)
      dry_run=true
      ;;
    --yes)
      confirmed=true
      ;;
    --purge)
      purge=true
      ;;
    --data-only)
      data_only=true
      ;;
    *)
      echo "ERROR: unsupported argument: ${arg}" >&2
      exit 1
      ;;
  esac
done

if [[ "${confirmed}" != "true" && "${dry_run}" != "true" ]]; then
  echo "ERROR: pass --yes to confirm uninstall." >&2
  exit 1
fi

safe_remove() {
  local target="$1"
  [[ -n "${target}" ]] || return 0
  if [[ "${target}" != "${HOME}/Nymphs-Sprite" &&
        "${target}" != "${HOME}/NymphsData/outputs/nymphs-sprite" &&
        "${target}" != "${HOME}/NymphsData/config/nymphs-sprite" &&
        "${target}" != "${HOME}/NymphsData/logs/nymphs-sprite" &&
        "${target}" != /tmp/nymphs-sprite-* ]]; then
    echo "ERROR: refusing to remove unexpected path: ${target}" >&2
    exit 1
  fi
  if [[ "${dry_run}" == "true" ]]; then
    echo "would_remove=${target}"
    return 0
  fi
  rm -rf "${target}"
}

if [[ "${data_only}" == "true" ]]; then
  safe_remove "${NYMPHS_SPRITE_OUTPUTS_ROOT}"
  safe_remove "${NYMPHS_SPRITE_CONFIG_DIR}"
  safe_remove "${NYMPHS_SPRITE_LOGS_DIR}"
  echo "data_deleted=true"
  exit 0
fi

safe_remove "${NYMPHS_SPRITE_INSTALL_DIR}"
echo "runtime_removed=true"

if [[ "${purge}" == "true" ]]; then
  safe_remove "${NYMPHS_SPRITE_OUTPUTS_ROOT}"
  safe_remove "${NYMPHS_SPRITE_CONFIG_DIR}"
  safe_remove "${NYMPHS_SPRITE_LOGS_DIR}"
  echo "data_deleted=true"
else
  echo "data_preserved=true"
fi

