#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if git -C "${REPO_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "${REPO_DIR}" pull --ff-only
fi

exec "${SCRIPT_DIR}/install_sprite_foundry.sh"
