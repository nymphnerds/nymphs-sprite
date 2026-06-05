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
asset=""
repo_id="mks0813/z-image-turbo-pixel-lora"
filename=""
library_filename=""
trigger=""
lora_scale=""
hf_token=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --asset|--download)
      if [[ $# -lt 2 ]]; then
        echo "$1 requires an asset id." >&2
        exit 2
      fi
      asset="${2:-}"
      shift 2
      ;;
    --asset=*|--download=*)
      asset="${1#*=}"
      shift
      ;;
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
      repo_id="mks0813/z-image-turbo-pixel-lora"
      filename="epoch-1.safetensors"
      shift
      ;;
    --skyasl|--pixel-artist-z)
      candidate="skyasl_pixel_artist"
      repo_id="SkyAsl/Pixel-artist-Z"
      filename="adapter_model.safetensors"
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage:
  nymphs_sprite_fetch_lora.sh --candidate mks0813_pixel_art
  nymphs_sprite_fetch_lora.sh --candidate skyasl_pixel_artist
  nymphs_sprite_fetch_lora.sh --candidate tarn59_pixel_art
  nymphs_sprite_fetch_lora.sh --repo owner/repo [--filename file.safetensors] [--trigger TOKEN] [--lora-scale 0.85]

Downloads a selected Z-Image Turbo-compatible sprite/pixel-art LoRA into:
  $HOME/LoRA/loras

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

if [[ -n "${asset}" ]]; then
  case "${asset}" in
    mks0813_pixel_art|skyasl_pixel_artist|tarn59_pixel_art)
      candidate="${asset}"
      ;;
    complete_sprite|all_sprite_assets)
      echo "asset_fetch_plan=LoRA:mks0813_pixel_art,LoRA:skyasl_pixel_artist,LoRA:tarn59_pixel_art,ControlNet:union,Depth:small"
      "${BASH_SOURCE[0]}" --candidate mks0813_pixel_art
      "${BASH_SOURCE[0]}" --candidate skyasl_pixel_artist
      "${BASH_SOURCE[0]}" --candidate tarn59_pixel_art
      "${SCRIPT_DIR}/nymphs_sprite_fetch_controlnet.sh"
      "${SCRIPT_DIR}/nymphs_sprite_fetch_depth_anything.sh" --small
      "${SCRIPT_DIR}/nymphs_sprite_select_lora.sh" --candidate mks0813_pixel_art
      echo "asset_fetch_complete=complete_sprite"
      echo "selected_lora=mks0813_pixel_art"
      exit 0
      ;;
    controlnet_union)
      exec "${SCRIPT_DIR}/nymphs_sprite_fetch_controlnet.sh"
      ;;
    depth_anything_small)
      exec "${SCRIPT_DIR}/nymphs_sprite_fetch_depth_anything.sh" --small
      ;;
    *)
      echo "ERROR: unknown sprite asset id: ${asset}" >&2
      exit 2
      ;;
  esac
fi

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
emit("library_filename", item.get("library_filename"))
emit("trigger", item.get("trigger"))
emit("lora_scale", item.get("recommended_lora_scale"))
PY
)"
  while IFS='=' read -r key value; do
    case "${key}" in
      repo_id) [[ -n "${value}" ]] && repo_id="${value}" ;;
      filename) filename="${value}" ;;
      library_filename) library_filename="${value}" ;;
      trigger) [[ -n "${trigger}" || -z "${value}" ]] || trigger="${value}" ;;
      lora_scale) [[ -n "${lora_scale}" || -z "${value}" ]] || lora_scale="${value}" ;;
    esac
  done <<< "${candidate_values}"
fi

if [[ -z "${repo_id}" ]]; then
  echo "ERROR: --repo is required." >&2
  exit 1
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
echo "MODEL FETCH STARTED: step=1/1 repo=${repo_id}"
echo "lora_candidate=${candidate:-custom}"
echo "lora_repo=${repo_id}"
echo "lora_filename=${filename:-auto}"
echo "lora_target_dir=${NYMPHS_SPRITE_LORA_DIR}"
echo "lora_library_filename=${library_filename:-auto}"

"${python_bin}" - "${repo_id}" "${filename}" "${NYMPHS_SPRITE_LORA_DIR}" "${trigger}" "${lora_scale}" "${NYMPHS_SPRITE_LORA_PRESET_FILE}" "${candidate:-custom}" "${library_filename:-}" <<'PY'
from __future__ import annotations

import shutil
import os
import json
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

try:
    from safetensors import safe_open
    from safetensors.torch import save_file
except Exception as exc:
    raise SystemExit(
        "ERROR: safetensors is required to normalize Z-Image LoRA files. "
        "Repair Nymphs Image/Z-Image, then rerun this script."
    ) from exc

repo_id = sys.argv[1]
filename = sys.argv[2].strip()
target_dir = Path(sys.argv[3]).expanduser()
trigger = sys.argv[4].strip()
lora_scale = sys.argv[5].strip()
preset_file = Path(sys.argv[6]).expanduser()
candidate = sys.argv[7].strip()
library_filename = sys.argv[8].strip()
target_dir.mkdir(parents=True, exist_ok=True)
repo_slug = repo_id.replace("/", "--")
cache_root = Path(os.environ.get("HF_HUB_CACHE") or os.environ.get("HF_HOME") or (Path.home() / "NymphsData" / "cache" / "huggingface")).expanduser()
repo_dir = cache_root / "nymphs-sprite-loras" / repo_slug
repo_dir.mkdir(parents=True, exist_ok=True)

if not library_filename:
    library_filename = f"{candidate}.safetensors" if candidate and candidate != "custom" else filename
if library_filename and not library_filename.lower().endswith(".safetensors"):
    library_filename += ".safetensors"


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
            "MODEL FETCH STATUS: "
            f"step=1/1 repo={repo_id} status=downloading "
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
                "MODEL FETCH STATUS: "
                f"step=1/1 repo={repo_id} status=retrying attempt={attempt + 1}/{attempts} "
                f"error={type(exc).__name__}",
                flush=True,
            )
            time.sleep(min(30, 5 * attempt))


def normalize_zimage_lora(input_path: Path, output_path: Path) -> dict:
    """Write a Nunchaku-friendly Z-Image LoRA copy.

    Public Z-Image LoRAs are not consistent about their key roots. Nunchaku's
    Z-Image mapper expects transformer-local names such as
    ``layers.0.attention.to_q.lora_A.weight``. Common HF files use PEFT
    ``base_model.model.`` or AI Toolkit ``diffusion_model.`` prefixes, and
    some use ``.default`` adapter-name segments. The shared LoRA library should
    contain the normalized runtime copy so Sprite, Nymphs Image, the LoRA
    module, and future UI all point at the same usable file.
    """

    prefix_rewrites = (
        ("base_model.model.", ""),
        ("diffusion_model.", ""),
        ("transformer.", ""),
    )
    suffix_rewrites = (
        (".lora_A.default.weight", ".lora_A.weight"),
        (".lora_B.default.weight", ".lora_B.weight"),
    )

    tensors = {}
    metadata = {}
    changed = False
    raw_ranks = set()
    with safe_open(input_path, framework="pt", device="cpu") as handle:
        metadata = dict(handle.metadata() or {})
        for key in handle.keys():
            new_key = key
            for old, new in prefix_rewrites:
                if new_key.startswith(old):
                    new_key = new + new_key[len(old):]
                    changed = True
                    break
            for old, new in suffix_rewrites:
                if new_key.endswith(old):
                    new_key = new_key[: -len(old)] + new
                    changed = True
                    break
            tensor = handle.get_tensor(key)
            if ".lora_A." in new_key and tensor.ndim == 2:
                raw_ranks.add(int(tensor.shape[0]))
            tensors[new_key] = tensor

    metadata["nymphs_source_repo"] = repo_id
    metadata["nymphs_source_filename"] = filename or input_path.name
    metadata["nymphs_zimage_lora_normalized"] = "true" if changed else "already-compatible"
    if raw_ranks:
        metadata["nymphs_lora_ranks"] = ",".join(str(value) for value in sorted(raw_ranks))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if input_path.resolve() == output_path.resolve():
        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        save_file(tensors, str(tmp_path), metadata=metadata)
        os.replace(tmp_path, output_path)
    else:
        save_file(tensors, str(output_path), metadata=metadata)
    return {
        "changed": changed,
        "tensor_count": len(tensors),
        "ranks": sorted(raw_ranks),
    }


def write_selection(dest: Path, normalization: dict) -> None:
    global trigger, lora_scale
    if not trigger:
        trigger = "pxlstl" if "mks0813" in repo_id.lower() else ("a pixel art character" if "skyasl" in repo_id.lower() else "Pixel art style.")
    if not lora_scale:
        lora_scale = "0.85"

    metadata = {
        "schema": "nymphs_lora.v1",
        "display_name": candidate if candidate and candidate != "custom" else dest.parent.name,
        "activation_text": trigger,
        "lora_type": "zimage_turbo_style",
        "source_module": "nymphs-sprite",
        "source_repo": repo_id,
        "source_filename": filename or dest.name,
        "base_model": "Tongyi-MAI/Z-Image-Turbo",
        "normalized_for": "zimage_nunchaku",
        "raw_lora_ranks": normalization["ranks"],
    }
    (dest.parent / "nymphs_lora.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    preset_file.parent.mkdir(parents=True, exist_ok=True)
    preset_file.write_text(
        "\n".join([
            f"NYMPHS_SPRITE_SELECTED_LORA_REPO={repo_id}",
            f"NYMPHS_SPRITE_SELECTED_LORA_CANDIDATE={candidate}",
            f"NYMPHS_SPRITE_SELECTED_LORA_FILE={dest.name}",
            f"NYMPHS_SPRITE_SELECTED_LORA_PATH={dest}",
            f"NYMPHS_SPRITE_SELECTED_LORA_TRIGGER={trigger}",
            f"NYMPHS_SPRITE_SELECTED_LORA_SCALE={lora_scale}",
            "",
        ]),
        encoding="utf-8",
    )


existing_dest: Path | None = None
if library_filename:
    library_id = Path(library_filename).stem
    maybe = target_dir / library_id / library_filename
    if maybe.is_file():
        existing_dest = maybe

if existing_dest is not None:
    print(f"LORA FETCH STATUS: repo={repo_id} status=using_existing_library path={existing_dest}", flush=True)
    normalization = normalize_zimage_lora(existing_dest, existing_dest)
    write_selection(existing_dest, normalization)
    print(f"MODEL FETCH COMPLETE: step=1/1 repo={repo_id}", flush=True)
    print(f"LORA FETCH COMPLETE: repo={repo_id} path={existing_dest} size={format_bytes(existing_dest.stat().st_size)}", flush=True)
    print(f"lora_repo={repo_id}")
    print(f"lora_candidate={candidate}")
    print(f"repo_id={repo_id}")
    print(f"lora_path={existing_dest}")
    print(f"lora_library_root={target_dir}")
    print(f"lora_trigger={trigger}")
    print(f"lora_scale={lora_scale}")
    print(f"lora_normalized={normalization['changed']}")
    print(f"lora_tensor_count={normalization['tensor_count']}")
    print(f"lora_ranks={','.join(str(value) for value in normalization['ranks']) or 'unknown'}")
    print(f"lora_preset_file={preset_file}")
    print(f"lora_repo_cache={format_bytes(local_summary(repo_dir)[1])}")
    raise SystemExit(0)


print("LORA FETCH STATUS: status=metadata repo=" + repo_id, flush=True)
available_safetensors: list[str] = []
try:
    info = HfApi().model_info(repo_id, files_metadata=True)
    available_safetensors = sorted(
        sibling.rfilename
        for sibling in (info.siblings or [])
        if sibling.rfilename.lower().endswith(".safetensors")
    )
    print(f"LORA FETCH PLAN: repo={repo_id} safetensors={len(available_safetensors)}", flush=True)
    for index, item in enumerate(available_safetensors[:12], start=1):
        print(f"LORA FETCH PLAN: file_{index}={item}", flush=True)
except Exception as exc:
    print(f"LORA FETCH STATUS: repo={repo_id} metadata_warning={type(exc).__name__}", flush=True)

if filename and available_safetensors and filename not in available_safetensors:
    print(
        "MODEL FETCH STATUS: "
        f"step=1/1 repo={repo_id} status=filename_missing "
        f"requested={filename} available={','.join(available_safetensors[:8])}",
        flush=True,
    )
    filename = ""

_, initial_size = local_summary(repo_dir)
print(
    "MODEL FETCH STATUS: "
    f"step=1/1 repo={repo_id} status=downloading "
    f"this_repo_cache={format_bytes(initial_size)} "
    f"active_download_files={active_download_files(repo_dir)}",
    flush=True,
)

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

if not library_filename:
    library_filename = downloaded.name
if not library_filename.lower().endswith(".safetensors"):
    library_filename += ".safetensors"
library_id = Path(library_filename).stem
dest = target_dir / library_id / library_filename

dest.parent.mkdir(parents=True, exist_ok=True)
normalization = normalize_zimage_lora(downloaded, dest)
write_selection(dest, normalization)

_, repo_size = local_summary(repo_dir)
print(f"MODEL FETCH COMPLETE: step=1/1 repo={repo_id}", flush=True)
print(f"LORA FETCH COMPLETE: repo={repo_id} path={dest} size={format_bytes(dest.stat().st_size)}", flush=True)
print(f"lora_repo={repo_id}")
print(f"lora_candidate={candidate}")
print(f"repo_id={repo_id}")
print(f"lora_path={dest}")
print(f"lora_library_root={target_dir}")
print(f"lora_trigger={trigger}")
print(f"lora_scale={lora_scale}")
print(f"lora_normalized={normalization['changed']}")
print(f"lora_tensor_count={normalization['tensor_count']}")
print(f"lora_ranks={','.join(str(value) for value in normalization['ranks']) or 'unknown'}")
print(f"lora_preset_file={preset_file}")
print(f"lora_repo_cache={format_bytes(repo_size)}")
PY
