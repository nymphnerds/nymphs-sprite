#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

if [[ -f "${SPRITE_FOUNDRY_UI_PID_FILE}" ]]; then
  pid="$(cat "${SPRITE_FOUNDRY_UI_PID_FILE}" 2>/dev/null || true)"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" >/dev/null 2>&1; then
    kill "${pid}" >/dev/null 2>&1 || true
  fi
  rm -f "${SPRITE_FOUNDRY_UI_PID_FILE}"
fi

echo "stopped=true"
