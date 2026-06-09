"""Tiny Nymphs Image client for the NymphsCore-backed Foundry fork."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 1800) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"cannot reach {url}: {exc.reason}") from exc


def latest_lora_path(nymphscore_url: str) -> str | None:
    data = request_json("GET", f"{nymphscore_url.rstrip('/')}/api/loras", timeout=20)
    runs = data.get("runs") or []
    if not runs:
        return None
    latest = runs[0].get("latest_file")
    return str(latest) if latest else None


def output_path(response: dict[str, Any]) -> Path | None:
    value = str(response.get("output_path") or "").strip()
    if not value:
        return None
    return Path(value).expanduser()


def generate_zimage(nymphscore_url: str, payload: dict[str, Any], timeout: int = 1800) -> dict[str, Any]:
    return request_json("POST", f"{nymphscore_url.rstrip('/')}/generate", payload=payload, timeout=timeout)
