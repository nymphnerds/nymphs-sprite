#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


DIRECTIONS = {
    "front": "facing the viewer, front view, looking at camera",
    "front_left": "facing front-left, 3/4 view from the left, looking slightly left",
    "left": "facing left, left side profile view",
    "back_left": "facing back-left, 3/4 rear view from the left",
    "back": "facing away from viewer, rear view, back of character",
    "back_right": "facing back-right, 3/4 rear view from the right",
    "right": "facing right, right side profile view",
    "front_right": "facing front-right, 3/4 view from the right, looking slightly right",
}


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
        raise SystemExit(f"ERROR: {method} {url} failed with HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"ERROR: cannot reach {url}: {exc.reason}") from exc


def latest_lora_path(zimage_url: str) -> str | None:
    data = request_json("GET", f"{zimage_url.rstrip('/')}/api/loras", timeout=20)
    runs = data.get("runs") or []
    if not runs:
        return None
    latest = runs[0].get("latest_file")
    return str(latest) if latest else None


def load_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an 8-direction sprite set through Nymphs Image Z-Image.")
    parser.add_argument("--zimage-url", default="http://127.0.0.1:8090")
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--subject-prompt", required=True)
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--lora-path", default="")
    parser.add_argument("--lora-trigger", default="pxlstl")
    parser.add_argument("--lora-scale", type=float, default=0.85)
    parser.add_argument("--seed", type=int, default=123456789)
    parser.add_argument("--seed-step", type=int, default=1)
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=9)
    parser.add_argument("--guidance-scale", type=float, default=0.0)
    parser.add_argument("--nunchaku-rank", type=int, default=32)
    parser.add_argument("--nunchaku-precision", default="auto", choices=["auto", "int4", "fp4"])
    parser.add_argument("--profile", default="")
    parser.add_argument("--directions", default=",".join(DIRECTIONS.keys()))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    zimage_url = args.zimage_url.rstrip("/")
    profile = {}
    if args.profile:
        profile = load_profile(Path(args.profile).expanduser())

    lora_path = args.lora_path.strip() or str(profile.get("lora_path") or "").strip()
    if not lora_path:
        lora_path = latest_lora_path(zimage_url) or ""
    if not lora_path:
        raise SystemExit("ERROR: no LoRA path supplied and /api/loras returned no available LoRAs.")

    lora_trigger = args.lora_trigger.strip() or str(profile.get("lora_trigger") or "").strip()
    direction_names = [item.strip() for item in args.directions.split(",") if item.strip()]
    invalid = [name for name in direction_names if name not in DIRECTIONS]
    if invalid:
        raise SystemExit(f"ERROR: unknown direction(s): {', '.join(invalid)}")

    batch_id = f"nymphs-sprite-{args.subject_id}-{uuid.uuid4().hex[:8]}"
    print(f"batch_id={batch_id}")
    print(f"lora_path={lora_path}")

    outputs = []
    for index, direction in enumerate(direction_names, start=1):
        prompt_parts = [
            lora_trigger,
            args.subject_prompt,
            DIRECTIONS[direction],
            "pixel art sprite",
            "game character sprite",
            "2D RPG",
            "clean readable silhouette",
            "centered full body character",
            "isolated figure",
            "crisp sprite design",
        ]
        prompt = ", ".join(part for part in prompt_parts if part)
        payload = {
            "provider": "zimage",
            "mode": "txt2img",
            "model_id": "Tongyi-MAI/Z-Image-Turbo",
            "nunchaku_rank": args.nunchaku_rank,
            "nunchaku_precision": args.nunchaku_precision,
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "guidance_scale": args.guidance_scale,
            "seed": args.seed + (index - 1) * args.seed_step,
            "prompt": prompt,
            "negative_prompt": args.negative_prompt,
            "lora_path": lora_path,
            "lora_scale": args.lora_scale,
            "batch_id": batch_id,
            "batch_label": f"Nymphs Sprite: {args.subject_id}",
            "batch_type": "sprite_direction",
            "item_label": direction,
            "item_index": index,
            "item_total": len(direction_names),
        }
        print(f"generate={direction} seed={payload['seed']}")
        response = request_json("POST", f"{zimage_url}/generate", payload=payload)
        outputs.append(response)
        print(f"output_{direction}={response.get('output_path')}")
        time.sleep(0.2)

    print(json.dumps({"status": "ok", "batch_id": batch_id, "outputs": outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

