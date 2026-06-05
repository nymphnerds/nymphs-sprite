#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

repo_id="${NYMPHS_SPRITE_CONTROLNET_REPO_ID}"

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

echo "MODEL FETCH STARTED: step=1/1 repo=${repo_id}"
echo "shared_hf_cache_dir=${NYMPHS3D_HF_CACHE_DIR}"

"${python_bin}" - "${repo_id}" "${NYMPHS3D_HF_CACHE_DIR}" <<'PY'
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

try:
    from huggingface_hub import snapshot_download
except Exception as exc:
    raise SystemExit(
        "ERROR: huggingface_hub is required. Install or repair Nymphs Image/Z-Image, "
        "then rerun this script."
    ) from exc

repo_id = sys.argv[1]
cache_dir = Path(sys.argv[2]).expanduser()
cache_dir.mkdir(parents=True, exist_ok=True)
local_dir = cache_dir / f"models--{repo_id.replace('/', '--')}"

def format_bytes(value: int) -> str:
    size = float(max(value, 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"

def local_summary(root: Path) -> tuple[int, int]:
    count = 0
    total = 0
    if not root.exists():
        return count, total
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        count += 1
        try:
            total += path.stat().st_size
        except OSError:
            pass
    return count, total

def active_download_files(root: Path) -> int:
    total = 0
    if not root.exists():
        return total
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith((".incomplete", ".lock", ".tmp", ".part")) or ".incomplete" in name:
            total += 1
    return total

def print_status() -> None:
    _, size = local_summary(local_dir)
    print(
        "MODEL FETCH STATUS: "
        f"step=1/1 repo={repo_id} status=downloading "
        f"this_repo_cache={format_bytes(size)} "
        f"active_download_files={active_download_files(local_dir)}",
        flush=True,
    )

def heartbeat(stop: threading.Event) -> None:
    while not stop.wait(5):
        print_status()

print_status()
stop = threading.Event()
thread = threading.Thread(target=heartbeat, args=(stop,), daemon=True)
thread.start()
try:
    path = snapshot_download(
        repo_id=repo_id,
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
finally:
    stop.set()
    thread.join(timeout=1)
print(f"MODEL FETCH COMPLETE: step=1/1 repo={repo_id}", flush=True)
print(f"repo_id={repo_id}")
print(f"controlnet_path={path}")
print(f"shared_hf_cache_dir={cache_dir}")
PY
