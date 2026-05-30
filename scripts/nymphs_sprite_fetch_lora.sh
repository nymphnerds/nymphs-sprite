#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

PROFILE_FILE="${NYMPHS_SPRITE_PROFILES_DIR}/zimage_turbo_lora_candidates.json"
if [[ ! -f "${PROFILE_FILE}" ]]; then
  PROFILE_FILE="$(cd "${SCRIPT_DIR}/.." && pwd)/profiles/zimage_turbo_lora_candidates.json"
fi

candidate=""
repo_id="mks0813/z-image-turbo-pixel-art-lora"
filename=""
trigger=""
lora_scale=""
hf_token=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --candidate|--model|--lora)
      if [[ $# -lt 2 ]]; then
        echo "$1 requires a LoRA candidate id." >&2
        exit 2
      fi
      candidate="${2:-}"
      shift 2
      ;;
    --candidate=*|--model=*|--lora=*)
      candidate="${1#*=}"
      shift
      ;;
    --repo)
      if [[ $# -lt 2 ]]; then
        echo "--repo requires a Hugging Face repo id." >&2
        exit 2
      fi
      repo_id="${2:-}"
      shift 2
      ;;
    --repo=*)
      repo_id="${1#*=}"
      shift
      ;;
    --filename)
      if [[ $# -lt 2 ]]; then
        echo "--filename requires a file name, or use --filename='' to auto-select." >&2
        exit 2
      fi
      filename="${2:-}"
      shift 2
      ;;
    --filename=*)
      filename="${1#*=}"
      shift
      ;;
    --trigger)
      if [[ $# -lt 2 ]]; then
        echo "--trigger requires a prompt trigger." >&2
        exit 2
      fi
      trigger="${2:-}"
      shift 2
      ;;
    --trigger=*)
      trigger="${1#*=}"
      shift
      ;;
    --lora-scale|--scale)
      if [[ $# -lt 2 ]]; then
        echo "$1 requires a numeric scale." >&2
        exit 2
      fi
      lora_scale="${2:-}"
      shift 2
      ;;
    --lora-scale=*|--scale=*)
      lora_scale="${1#*=}"
      shift
      ;;
    --hf_token|--hf-token)
      if [[ $# -lt 2 || "${2:-}" == --* ]]; then
        hf_token=""
        shift 1
      else
        hf_token="${2:-}"
        shift 2
      fi
      ;;
    --hf_token=*|--hf-token=*)
      hf_token="${1#*=}"
      shift
      ;;
    --tarn59)
      candidate="tarn59_pixel_art"
      repo_id="tarn59/pixel_art_style_lora_z_image_turbo"
      filename=""
      shift
      ;;
    --mks0813)
      candidate="mks0813_pixel_art"
      repo_id="mks0813/z-image-turbo-pixel-art-lora"
      filename="z-image-turbo-pixel-art-lora.safetensors"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  nymphs_sprite_fetch_lora.sh --candidate mks0813_pixel_art
  nymphs_sprite_fetch_lora.sh --candidate tarn59_pixel_art
  nymphs_sprite_fetch_lora.sh --repo owner/repo [--filename file.safetensors] [--trigger TOKEN] [--lora-scale 0.85]

Downloads a selected Z-Image Turbo-compatible sprite/pixel-art LoRA into:
  $HOME/LoRA/loras/nymphs-sprite

Known candidates live in profiles/zimage_turbo_lora_candidates.json.
If --filename is omitted for a custom repo, the first .safetensors in the repo
snapshot is selected.
EOF
      exit 0
      ;;
    *)
      echo "ERROR: unsupported argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -n "${candidate}" && -f "${PROFILE_FILE}" ]]; then
  candidate_values="$(python3 - "${PROFILE_FILE}" "${candidate}" <<'PY'
from __future__ import annotations

import json
import sys

profile_file, candidate = sys.argv[1], sys.argv[2]
with open(profile_file, "r", encoding="utf-8") as handle:
    data = json.load(handle)
item = (data.get("candidates") or {}).get(candidate)
if not item:
    raise SystemExit(f"ERROR: unknown LoRA candidate: {candidate}")

def emit(key: str, value) -> None:
    if value is None:
        value = ""
    print(f"{key}={str(value)}")

emit("repo_id", item.get("repo_id"))
emit("filename", item.get("filename"))
emit("trigger", item.get("trigger"))
emit("lora_scale", item.get("recommended_lora_scale"))
PY
)"
  while IFS='=' read -r key value; do
    case "${key}" in
      repo_id) [[ -n "${value}" ]] && repo_id="${value}" ;;
      filename) filename="${value}" ;;
      trigger) [[ -n "${trigger}" || -z "${value}" ]] || trigger="${value}" ;;
      lora_scale) [[ -n "${lora_scale}" || -z "${value}" ]] || lora_scale="${value}" ;;
    esac
  done <<< "${candidate_values}"
fi

if [[ -z "${repo_id}" ]]; then
  echo "ERROR: --repo is required." >&2
  exit 1
fi

if [[ -z "${filename}" && "${repo_id}" == "mks0813/z-image-turbo-pixel-art-lora" ]]; then
  filename="z-image-turbo-pixel-art-lora.safetensors"
fi

nymphs_sprite_ensure_dirs
python_bin="$(nymphs_sprite_python_bin)"

export HF_HUB_DISABLE_PROGRESS_BARS="${HF_HUB_DISABLE_PROGRESS_BARS:-1}"
if [[ -z "${hf_token}" && -n "${NYMPHS3D_HF_TOKEN:-}" ]]; then
  hf_token="${NYMPHS3D_HF_TOKEN}"
fi
if [[ -n "${hf_token}" ]]; then
  export HF_TOKEN="${hf_token}"
  export HUGGING_FACE_HUB_TOKEN="${hf_token}"
fi

echo "LORA FETCH STARTED: repo=${repo_id} target=${NYMPHS_SPRITE_LORA_DIR}"
echo "lora_candidate=${candidate:-custom}"
echo "lora_repo=${repo_id}"
echo "lora_filename=${filename:-auto}"
echo "lora_target_dir=${NYMPHS_SPRITE_LORA_DIR}"

"${python_bin}" - "${repo_id}" "${filename}" "${NYMPHS_SPRITE_LORA_DIR}" "${trigger}" "${lora_scale}" "${NYMPHS_SPRITE_LORA_PRESET_FILE}" <<'PY'
from __future__ import annotations

import shutil
import sys
import threading
import time
from pathlib import Path

try:
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download
except Exception as exc:
    raise SystemExit(
        "ERROR: huggingface_hub is required. Install or repair Nymphs Image/Z-Image, "
        "then rerun this script."
    ) from exc

repo_id = sys.argv[1]
filename = sys.argv[2].strip()
target_dir = Path(sys.argv[3]).expanduser()
trigger = sys.argv[4].strip()
lora_scale = sys.argv[5].strip()
preset_file = Path(sys.argv[6]).expanduser()
target_dir.mkdir(parents=True, exist_ok=True)
repo_slug = repo_id.replace("/", "--")
repo_dir = target_dir / repo_slug
repo_dir.mkdir(parents=True, exist_ok=True)


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
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith((".incomplete", ".lock", ".tmp", ".part")) or ".incomplete" in name:
            total += 1
    return total


def heartbeat(stop: threading.Event) -> None:
    while not stop.wait(5):
        _, size = local_summary(repo_dir)
        print(
            "LORA FETCH STATUS: "
            f"repo={repo_id} status=downloading "
            f"this_repo_cache={format_bytes(size)} "
            f"active_download_files={active_download_files(repo_dir)}",
            flush=True,
        )


def with_retries(action):
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            return action()
        except Exception as exc:
            if attempt >= attempts:
                raise
            print(
                "LORA FETCH STATUS: "
                f"repo={repo_id} status=retrying attempt={attempt + 1}/{attempts} "
                f"error={type(exc).__name__}",
                flush=True,
            )
            time.sleep(min(30, 5 * attempt))


print("LORA FETCH STATUS: status=metadata repo=" + repo_id, flush=True)
try:
    info = HfApi().model_info(repo_id, files_metadata=True)
    safetensors = sorted(
        sibling.rfilename
        for sibling in (info.siblings or [])
        if sibling.rfilename.lower().endswith(".safetensors")
    )
    print(f"LORA FETCH PLAN: repo={repo_id} safetensors={len(safetensors)}", flush=True)
    for index, item in enumerate(safetensors[:12], start=1):
        print(f"LORA FETCH PLAN: file_{index}={item}", flush=True)
except Exception as exc:
    print(f"LORA FETCH STATUS: repo={repo_id} metadata_warning={type(exc).__name__}", flush=True)

stop = threading.Event()
thread = threading.Thread(target=heartbeat, args=(stop,), daemon=True)
thread.start()
try:
    if filename:
        downloaded = Path(with_retries(lambda: hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(repo_dir),
            force_download=False,
        )))
    else:
        snapshot = Path(with_retries(lambda: snapshot_download(
            repo_id=repo_id,
            local_dir=str(repo_dir),
            local_dir_use_symlinks=False,
            allow_patterns=["*.safetensors"],
        )))
        matches = sorted(snapshot.rglob("*.safetensors"))
        if not matches:
            raise SystemExit(f"ERROR: no .safetensors files found in {repo_id}.")
        downloaded = matches[0]
finally:
    stop.set()
    thread.join(timeout=1)

dest = repo_dir / downloaded.name
if filename:
    dest = downloaded

dest.parent.mkdir(parents=True, exist_ok=True)
if downloaded != dest and (not dest.exists() or dest.stat().st_size != downloaded.stat().st_size):
    shutil.copy2(downloaded, dest)

if not trigger:
    trigger = "pxlstl" if "mks0813" in repo_id.lower() else "Pixel art style."
if not lora_scale:
    lora_scale = "0.85"

preset_file.parent.mkdir(parents=True, exist_ok=True)
preset_file.write_text(
    "\n".join([
        f"NYMPHS_SPRITE_SELECTED_LORA_REPO={repo_id}",
        f"NYMPHS_SPRITE_SELECTED_LORA_FILE={dest.name}",
        f"NYMPHS_SPRITE_SELECTED_LORA_PATH={dest}",
        f"NYMPHS_SPRITE_SELECTED_LORA_TRIGGER={trigger}",
        f"NYMPHS_SPRITE_SELECTED_LORA_SCALE={lora_scale}",
        "",
    ]),
    encoding="utf-8",
)

_, repo_size = local_summary(repo_dir)
print(f"LORA FETCH COMPLETE: repo={repo_id} path={dest} size={format_bytes(dest.stat().st_size)}", flush=True)
print(f"lora_repo={repo_id}")
print(f"repo_id={repo_id}")
print(f"lora_path={dest}")
print(f"lora_trigger={trigger}")
print(f"lora_scale={lora_scale}")
print(f"lora_preset_file={preset_file}")
print(f"lora_repo_cache={format_bytes(repo_size)}")
PY
