#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

repo_id="alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo_id="${2:-}"
      shift 2
      ;;
    --repo=*)
      repo_id="${1#*=}"
      shift
      ;;
    *)
      echo "ERROR: unsupported argument: $1" >&2
      exit 1
      ;;
  esac
done

nymphs_sprite_ensure_dirs
python_bin="$(nymphs_sprite_python_bin)"

"${python_bin}" - "${repo_id}" "${NYMPHS_SPRITE_CONTROLNET_DIR}" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except Exception as exc:
    raise SystemExit(
        "ERROR: huggingface_hub is required. Install or repair Nymphs Image/Z-Image, "
        "then rerun this script."
    ) from exc

repo_id = sys.argv[1]
target_dir = Path(sys.argv[2]).expanduser()
target_dir.mkdir(parents=True, exist_ok=True)
local_dir = target_dir / repo_id.replace("/", "--")
path = snapshot_download(
    repo_id=repo_id,
    local_dir=str(local_dir),
    local_dir_use_symlinks=False,
    allow_patterns=[
        "*.json",
        "*.txt",
        "*.md",
        "*.safetensors",
        "*.bin",
        "*.model",
        "*.png",
        "*.jpg",
        "*.jpeg",
    ],
)
print(f"repo_id={repo_id}")
print(f"controlnet_path={path}")
PY
