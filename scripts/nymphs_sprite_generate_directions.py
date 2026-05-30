#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
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


def safe_name(value: str, fallback: str = "sprite") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return cleaned[:80] or fallback


def response_output_path(response: dict[str, Any]) -> Path | None:
    value = str(response.get("output_path") or "").strip()
    if not value:
        return None
    return Path(value).expanduser()


def copy_direction_image(source: Path, target_dir: Path, index: int, direction: str) -> Path | None:
    if not source.exists() or not source.is_file():
        return None
    suffix = source.suffix or ".png"
    target = target_dir / f"{index:02d}_{direction}{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def write_contact_sheet(items: list[dict[str, Any]], target_path: Path, cell_size: int = 192) -> Path | None:
    image_items = [item for item in items if item.get("artifact_path")]
    if not image_items:
        return None
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except Exception:
        print("contact_sheet=skipped reason=Pillow-unavailable")
        return None

    columns = min(4, max(1, len(image_items)))
    rows = (len(image_items) + columns - 1) // columns
    label_h = 28
    gutter = 12
    width = columns * cell_size + (columns + 1) * gutter
    height = rows * (cell_size + label_h) + (rows + 1) * gutter
    sheet = Image.new("RGB", (width, height), (12, 17, 16))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, item in enumerate(image_items):
        row, col = divmod(index, columns)
        x = gutter + col * (cell_size + gutter)
        y = gutter + row * (cell_size + label_h + gutter)
        path = Path(str(item["artifact_path"]))
        try:
            with Image.open(path) as handle:
                image = ImageOps.contain(handle.convert("RGBA"), (cell_size, cell_size))
                px = x + (cell_size - image.width) // 2
                py = y + (cell_size - image.height) // 2
                sheet.paste(image, (px, py), image)
        except Exception as exc:
            draw.text((x, y + 8), f"load failed: {type(exc).__name__}", fill=(255, 141, 141), font=font)
        label = str(item.get("direction") or "")
        draw.text((x, y + cell_size + 8), label, fill=(215, 231, 223), font=font)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target_path)
    return target_path


def write_sprite_artifacts(
    *,
    outputs_root: Path,
    subject_id: str,
    batch_id: str,
    lora_path: str,
    lora_trigger: str,
    args: argparse.Namespace,
    generated: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_dir = outputs_root.expanduser() / safe_name(subject_id) / batch_id
    directions_dir = batch_dir / "directions"
    copied_items: list[dict[str, Any]] = []

    for item in generated:
        response = item["response"]
        source = response_output_path(response)
        artifact_path = None
        if source is not None and args.copy_images:
            artifact_path = copy_direction_image(source, directions_dir, int(item["index"]), str(item["direction"]))
        copied_items.append(
            {
                "direction": item["direction"],
                "index": item["index"],
                "seed": item["seed"],
                "prompt": item["prompt"],
                "source_output_path": str(source) if source else "",
                "source_metadata_path": str(response.get("metadata_path") or ""),
                "source_url": str(response.get("url") or ""),
                "artifact_path": str(artifact_path) if artifact_path else "",
                "zimage_response": response,
            }
        )

    contact_sheet = write_contact_sheet(copied_items, batch_dir / "contact_sheet.png", args.contact_cell_size)
    manifest = {
        "schema": "nymphs-sprite.batch.v1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "batch_id": batch_id,
        "subject_id": subject_id,
        "subject_prompt": args.subject_prompt,
        "negative_prompt": args.negative_prompt,
        "model_id": "Tongyi-MAI/Z-Image-Turbo",
        "lora_path": lora_path,
        "lora_trigger": lora_trigger,
        "lora_scale": args.lora_scale,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "base_seed": args.seed,
        "seed_step": args.seed_step,
        "directions": copied_items,
        "contact_sheet": str(contact_sheet) if contact_sheet else "",
    }
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = batch_dir / "sprite_batch.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "batch_dir": str(batch_dir),
        "manifest_path": str(manifest_path),
        "contact_sheet": str(contact_sheet) if contact_sheet else "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an 8-direction sprite set through Nymphs Image Z-Image.")
    parser.add_argument("--zimage-url", default="http://127.0.0.1:8090")
    parser.add_argument("--outputs-root", default=str(Path.home() / "NymphsData" / "outputs" / "nymphs-sprite"))
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
    parser.add_argument("--contact-cell-size", type=int, default=192)
    parser.add_argument("--copy-images", action=argparse.BooleanOptionalAction, default=True)
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
    generated = []
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
        generated.append(
            {
                "direction": direction,
                "index": index,
                "seed": payload["seed"],
                "prompt": prompt,
                "response": response,
            }
        )
        print(f"output_{direction}={response.get('output_path')}")
        time.sleep(0.2)

    artifacts = write_sprite_artifacts(
        outputs_root=Path(args.outputs_root),
        subject_id=args.subject_id,
        batch_id=batch_id,
        lora_path=lora_path,
        lora_trigger=lora_trigger,
        args=args,
        generated=generated,
    )
    print(f"sprite_batch_dir={artifacts['batch_dir']}")
    print(f"sprite_manifest={artifacts['manifest_path']}")
    if artifacts["contact_sheet"]:
        print(f"sprite_contact_sheet={artifacts['contact_sheet']}")

    print(json.dumps({"status": "ok", "batch_id": batch_id, "outputs": outputs, "artifacts": artifacts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
