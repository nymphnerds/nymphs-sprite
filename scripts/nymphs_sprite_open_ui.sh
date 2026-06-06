#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

server_script="${SCRIPT_DIR}/nymphs_sprite_ui_server.py"
ui_path="${NYMPHS_SPRITE_UI_DIR}/manager.html"

if [[ ! -f "${ui_path}" ]]; then
  echo "ERROR: Nymphs Sprite Manager UI is missing. Run Install, Update, or Repair." >&2
  exit 1
fi

if [[ ! -f "${server_script}" ]]; then
  echo "ERROR: Nymphs Sprite UI server is missing. Run Install, Update, or Repair." >&2
  exit 1
fi

nymphs_sprite_ensure_dirs

if ! nymphs_sprite_probe_url "${NYMPHS_SPRITE_UI_URL}/server_info" >/dev/null 2>&1; then
  if [[ -f "${NYMPHS_SPRITE_UI_PID_FILE}" ]]; then
    old_pid="$(cat "${NYMPHS_SPRITE_UI_PID_FILE}" 2>/dev/null || true)"
    if [[ -n "${old_pid}" ]] && ! kill -0 "${old_pid}" 2>/dev/null; then
      rm -f "${NYMPHS_SPRITE_UI_PID_FILE}"
    fi
  fi

  nohup python3 "${server_script}" \
    --host "${NYMPHS_SPRITE_UI_HOST}" \
    --port "${NYMPHS_SPRITE_UI_PORT}" \
    --root "${NYMPHS_SPRITE_INSTALL_DIR}" \
    >> "${NYMPHS_SPRITE_UI_LOG_FILE}" 2>&1 &
  printf '%s\n' "$!" > "${NYMPHS_SPRITE_UI_PID_FILE}"

  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if nymphs_sprite_probe_url "${NYMPHS_SPRITE_UI_URL}/server_info" >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done
fi

if ! nymphs_sprite_probe_url "${NYMPHS_SPRITE_UI_URL}/server_info" >/dev/null 2>&1; then
  echo "ERROR: Nymphs Sprite UI server did not start. See ${NYMPHS_SPRITE_UI_LOG_FILE}." >&2
  exit 1
fi

echo "url=${NYMPHS_SPRITE_UI_URL}/nymph"
echo "module_ui_url=${NYMPHS_SPRITE_UI_URL}/nymph"
echo "Nymphs Sprite UI is running."
