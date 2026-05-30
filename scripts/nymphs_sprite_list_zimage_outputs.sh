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

python3 - "${NYMPHS_SPRITE_ZIMAGE_URL}" "${limit}" <<'PY'
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")
try:
    limit = max(1, min(200, int(sys.argv[2])))
except Exception:
    limit = 80

url = f"{base_url}/api/outputs?limit={limit}"
try:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
except urllib.error.URLError as exc:
    print(json.dumps({"outputs": [], "error": str(exc.reason)}))
    raise SystemExit(0)

outputs = []
for item in body.get("outputs") or []:
    record = dict(item)
    raw_url = str(record.get("url") or "")
    if raw_url.startswith("/"):
        record["url"] = f"{base_url}{raw_url}"
    outputs.append(record)

print(json.dumps({"outputs": outputs}, separators=(",", ":")))
PY
