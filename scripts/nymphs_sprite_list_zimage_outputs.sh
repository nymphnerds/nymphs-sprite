#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/_nymphs_sprite_common.sh"

limit="${1:-80}"
case "${limit}" in
  --limit)
    limit="${2:-80}"
    ;;
  --limit=*)
    limit="${limit#*=}"
    ;;
esac

python3 - "${NYMPHS_SPRITE_ZIMAGE_URL}" "${limit}" "${NYMPHS_DATA_ROOT}/outputs/zimage" "${HOME}/Z-Image/outputs" "${HOME}/NymphsModules/zimage/outputs" <<'PY'
from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

base_url = sys.argv[1].rstrip("/")
try:
    limit = max(1, min(200, int(sys.argv[2])))
except Exception:
    limit = 80
fallback_roots = [Path(item).expanduser() for item in sys.argv[3:] if item.strip()]

image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}


def output_url(path: Path, root: Path, use_api_urls: bool) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        rel = path.name
    if use_api_urls and root == fallback_roots[0] and base_url:
        from urllib.parse import quote

        return f"{base_url}/outputs/{quote(rel, safe='/')}"
    return path.resolve().as_uri()


def metadata_for(path: Path) -> dict:
    metadata_path = path.with_suffix(".json")
    if not metadata_path.is_file():
        return {}
    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def filesystem_outputs(use_api_urls: bool = False) -> list[dict]:
    seen: set[str] = set()
    records: list[dict] = []
    for root in fallback_roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in image_suffixes:
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            stat = path.stat()
            metadata = metadata_for(path)
            try:
                rel = path.resolve().relative_to(root.resolve()).as_posix()
            except Exception:
                rel = path.name
            records.append(
                {
                    "name": metadata.get("item_label") or metadata.get("batch_label") or path.stem,
                    "path": str(path),
                    "relative_path": rel,
                    "url": output_url(path, root, use_api_urls),
                    "created": metadata.get("created") or metadata.get("created_at") or stat.st_mtime,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "mime_type": mimetypes.guess_type(path.name)[0] or "image/png",
                    "metadata": metadata,
                    "metadata_path": str(path.with_suffix(".json")) if path.with_suffix(".json").is_file() else "",
                    "batch_id": metadata.get("batch_id", ""),
                    "batch_type": metadata.get("batch_type", ""),
                    "batch_label": metadata.get("batch_label", ""),
                    "item_label": metadata.get("item_label", ""),
                    "item_index": metadata.get("item_index", 0),
                    "folder": Path(rel).parent.as_posix() if Path(rel).parent.as_posix() != "." else "",
                }
            )
    records.sort(key=lambda item: float(item.get("mtime") or 0), reverse=True)
    return records[:limit]

url = f"{base_url}/api/outputs?limit={limit}"
try:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
except urllib.error.URLError as exc:
    print(json.dumps({"outputs": filesystem_outputs(use_api_urls=False), "source": "filesystem", "api_error": str(exc.reason)}))
    raise SystemExit(0)

outputs = []
for item in body.get("outputs") or []:
    record = dict(item)
    raw_url = str(record.get("url") or "")
    if raw_url.startswith("/"):
        record["url"] = f"{base_url}{raw_url}"
    outputs.append(record)

if outputs:
    print(json.dumps({"outputs": outputs, "source": "api"}, separators=(",", ":")))
else:
    print(json.dumps({"outputs": filesystem_outputs(use_api_urls=True), "source": "filesystem-empty-api"}, separators=(",", ":")))
PY
