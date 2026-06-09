#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

root="$(sprite_foundry_root)"
sprite_foundry_ensure_dirs
sprite_foundry_touch_log

if ! sprite_foundry_probe_url "${SPRITE_FOUNDRY_UI_URL}/health" >/dev/null 2>&1; then
  if [[ -f "${SPRITE_FOUNDRY_UI_PID_FILE}" ]]; then
    old_pid="$(cat "${SPRITE_FOUNDRY_UI_PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${old_pid}" ]] && ! kill -0 "${old_pid}" >/dev/null 2>&1; then
      rm -f "${SPRITE_FOUNDRY_UI_PID_FILE}"
    fi
  fi
  nohup python3 "${root}/scripts/sprite_foundry_ui_server.py" \
    --host "${SPRITE_FOUNDRY_UI_HOST}" \
    --port "${SPRITE_FOUNDRY_UI_PORT}" \
    --root "${root}" \
    >> "${SPRITE_FOUNDRY_UI_LOG_FILE}" 2>&1 &
  printf '%s\n' "$!" > "${SPRITE_FOUNDRY_UI_PID_FILE}"
fi

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if sprite_foundry_probe_url "${SPRITE_FOUNDRY_UI_URL}/health" >/dev/null 2>&1; then
    echo "result=local_url"
    echo "url=${SPRITE_FOUNDRY_UI_URL}/nymph"
    echo "module_ui_url=${SPRITE_FOUNDRY_UI_URL}/nymph"
    echo "ui_url=${SPRITE_FOUNDRY_UI_URL}/nymph"
    exit 0
  fi
  sleep 0.25
done

rm -f "${SPRITE_FOUNDRY_UI_PID_FILE}"
echo "ERROR: ${SPRITE_FOUNDRY_MODULE_NAME} UI did not become healthy at ${SPRITE_FOUNDRY_UI_URL}." >&2
echo "log=${SPRITE_FOUNDRY_UI_LOG_FILE}" >&2
exit 1
