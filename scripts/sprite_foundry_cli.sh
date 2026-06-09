#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_sprite_foundry_common.sh"

command_name="status"
run_id=""
direction=""
attempt_id=""
code=""
subject_id=""
config=""
extra_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --command)
      command_name="$2"
      shift 2
      ;;
    --run-id)
      run_id="$2"
      shift 2
      ;;
    --direction)
      direction="$2"
      shift 2
      ;;
    --attempt-id)
      attempt_id="$2"
      shift 2
      ;;
    --code)
      code="$2"
      shift 2
      ;;
    --subject-id)
      subject_id="$2"
      shift 2
      ;;
    --config)
      config="$2"
      shift 2
      ;;
    *)
      extra_args+=("$1")
      shift
      ;;
  esac
done

root="$(sprite_foundry_root)"
python_bin="$(sprite_foundry_python_bin)"
sprite_foundry_ensure_dirs
sprite_foundry_touch_log

require_run() {
  if [[ -z "${run_id}" ]]; then
    echo "ERROR: --run-id is required for ${command_name}" >&2
    exit 1
  fi
}

require_direction() {
  if [[ -z "${direction}" ]]; then
    echo "ERROR: --direction is required for ${command_name}" >&2
    exit 1
  fi
}

require_attempt() {
  if [[ -z "${attempt_id}" ]]; then
    echo "ERROR: --attempt-id is required for ${command_name}" >&2
    exit 1
  fi
}

require_code() {
  if [[ -z "${code}" ]]; then
    echo "ERROR: --code is required for ${command_name}" >&2
    exit 1
  fi
}

resolve_attempt_id() {
  if [[ -n "${attempt_id}" ]]; then
    printf '%s\n' "${attempt_id}"
    return 0
  fi

  require_run
  require_direction

  local resolved
  resolved="$(
    "${python_bin}" - "${root}/foundry.db" "${run_id}" "${direction}" <<'PY'
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
run_id = sys.argv[2]
direction = sys.argv[3]
if not db_path.is_file():
    raise SystemExit(0)

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
row = conn.execute(
    """
    SELECT id
      FROM attempts
     WHERE run_id = ? AND direction = ?
     ORDER BY
       CASE
         WHEN state IN ('raw_review_pending', 'pixel_review_pending', 'finish_review_pending') THEN 0
         ELSE 1
       END,
       id DESC
     LIMIT 1
    """,
    (run_id, direction),
).fetchone()
conn.close()
if row:
    print(row["id"])
PY
  )"
  if [[ -z "${resolved}" ]]; then
    echo "ERROR: no attempt found for run '${run_id}' direction '${direction}'." >&2
    exit 1
  fi
  printf '%s\n' "${resolved}"
}

cd "${root}"
case "${command_name}" in
  status|metrics|drift)
    cmd=("${python_bin}" -m foundry.cli "${command_name}")
    if [[ -n "${run_id}" ]]; then
      cmd+=("${run_id}")
    fi
    ;;
  check|review-show|lineage|winner|produce|export|ship-check|ship-export)
    require_run
    cmd=("${python_bin}" -m foundry.cli "${command_name}" "${run_id}")
    ;;
  batch-accept)
    require_run
    cmd=("${python_bin}" -m foundry.cli batch-accept "${run_id}")
    ;;
  batch-reject)
    require_run
    require_code
    cmd=("${python_bin}" -m foundry.cli batch-reject "${run_id}" "--code" "${code}")
    ;;
  review-accept)
    attempt_id="$(resolve_attempt_id)"
    cmd=("${python_bin}" -m foundry.cli review-accept "${attempt_id}")
    ;;
  review-reject)
    require_code
    attempt_id="$(resolve_attempt_id)"
    cmd=("${python_bin}" -m foundry.cli review-reject "${attempt_id}" "--code" "${code}")
    ;;
  attempt-detail|story)
    require_attempt
    cmd=("${python_bin}" -m foundry.cli "${command_name}" "${attempt_id}")
    ;;
  subject-add)
    if [[ -z "${subject_id}" ]]; then
      echo "ERROR: --subject-id is required for subject-add" >&2
      exit 1
    fi
    cmd=("${python_bin}" -m foundry.cli subject-add "${subject_id}" "--name" "${subject_id}")
    ;;
  *)
    echo "ERROR: unsupported Foundry command: ${command_name}" >&2
    exit 2
    ;;
esac

cmd+=("${extra_args[@]}")
printf 'foundry_command=%s\n' "${command_name}" >> "${SPRITE_FOUNDRY_LOG_FILE}"
exec "${cmd[@]}"
