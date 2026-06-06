#!/usr/bin/env python3
"""Nymphs Sprite direction runner.

The post-processing stage adapts the MIT-licensed Sprite Foundry normalization
method: background cleanup, square crop, nearest-neighbor sprite resize,
mechanical alpha checks, and review/contact sheets.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
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

ORDERED_DIRECTIONS = list(DIRECTIONS.keys())
STYLE_SUFFIX = (
    "pixel art sprite, game character sprite, 2D RPG, clean readable silhouette, "
    "centered full body character, isolated figure, bright green background, "
    "crisp sprite design, HD-2D inspired, single character only"
)
NEGATIVE_BG = "white background, gray background, grey background, beige background, gradient background"


class RequestJsonError(RuntimeError):
    def __init__(self, method: str, url: str, status: int | None, body: str):
        self.method = method
        self.url = url
        self.status = status
        self.body = body
        status_text = f"HTTP {status}" if status is not None else "request error"
        super().__init__(f"ERROR: {method} {url} failed with {status_text}: {body}")


def request_json_raw(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 1800,
) -> dict[str, Any]:
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
        raise RequestJsonError(method, url, exc.code, body) from exc
    except urllib.error.URLError as exc:
        raise RequestJsonError(method, url, None, str(exc.reason)) from exc


def request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: int = 1800) -> dict[str, Any]:
    try:
        return request_json_raw(method, url, payload=payload, timeout=timeout)
    except RequestJsonError as exc:
        if exc.status is None:
            raise SystemExit(f"ERROR: cannot reach {url}: {exc.body}") from exc
        raise SystemExit(str(exc)) from exc


def latest_lora_path(zimage_url: str) -> str | None:
    data = request_json("GET", f"{zimage_url.rstrip('/')}/api/loras", timeout=20)
    runs = data.get("runs") or []
    if not runs:
        return None
    latest = runs[0].get("latest_file")
    return str(latest) if latest else None


def ensure_zimage_model_loaded(zimage_url: str, args: argparse.Namespace) -> None:
    payload = {
        "model_id": "Tongyi-MAI/Z-Image-Turbo",
        "nunchaku_rank": args.nunchaku_rank,
        "nunchaku_precision": args.nunchaku_precision,
    }
    response = request_json("POST", f"{zimage_url.rstrip('/')}/api/model/load", payload=payload, timeout=1800)
    if not response.get("loaded") and response.get("restart") == "scheduled":
        print(
            "zimage_model_restart="
            f"{payload['model_id']} precision={payload['nunchaku_precision']} rank={payload['nunchaku_rank']}",
            flush=True,
        )
        for _attempt in range(45):
            time.sleep(1.0)
            try:
                request_json("GET", f"{zimage_url.rstrip('/')}/health", timeout=5)
                break
            except SystemExit:
                continue
        response = request_json("POST", f"{zimage_url.rstrip('/')}/api/model/load", payload=payload, timeout=1800)
    if response.get("loaded"):
        print(
            "zimage_model_loaded="
            f"{payload['model_id']} precision={payload['nunchaku_precision']} rank={payload['nunchaku_rank']}",
            flush=True,
        )
        return
    raise SystemExit(f"ERROR: Z-Image did not load the selected model: {response}")


def load_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_name(value: str, fallback: str = "sprite") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return cleaned[:80] or fallback


def split_source_images(value: str) -> list[Path]:
    text = value.strip()
    if not text:
        return []
    separator = "|" if "|" in text else ","
    paths = []
    for item in text.split(separator):
        clean = item.strip()
        if clean and not clean.startswith(("http://", "https://", "manual:")):
            paths.append(Path(clean).expanduser())
    return paths


def source_direction_name(path: Path, index: int) -> str:
    stem = safe_name(path.stem, f"source-{index}").lower()
    for direction in sorted(ORDERED_DIRECTIONS, key=len, reverse=True):
        if direction in stem:
            return direction
    return f"source_{index:02d}"


def image_data_url(path: Path) -> str:
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def control_sources_by_direction(paths: list[Path], directions: list[str]) -> dict[str, Path]:
    by_direction: dict[str, Path] = {}
    ordered_fallback: list[Path] = []
    for index, path in enumerate(paths, start=1):
        direction = source_direction_name(path, index)
        if direction in DIRECTIONS and direction not in by_direction:
            by_direction[direction] = path
        ordered_fallback.append(path)
    for index, direction in enumerate(directions):
        if direction not in by_direction and index < len(ordered_fallback):
            by_direction[direction] = ordered_fallback[index]
    return by_direction


def response_output_path(response: dict[str, Any]) -> Path | None:
    value = str(response.get("output_path") or "").strip()
    if not value:
        return None
    return Path(value).expanduser()


def foundry_negative_prompt(negative_prompt: str) -> str:
    negative = negative_prompt.strip()
    return f"{negative}, {NEGATIVE_BG}" if negative else NEGATIVE_BG


def copy_direction_image(source: Path, target_dir: Path, index: int, direction: str, label_suffix: str = "") -> Path | None:
    if not source.exists() or not source.is_file():
        return None
    suffix = source.suffix or ".png"
    target = target_dir / f"{index:02d}_{direction}{label_suffix}{suffix}"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageOps
    except Exception:
        return None
    return Image, ImageDraw, ImageFont, ImageOps


def load_default_font(ImageFont, size: int):
    for name in ("consola.ttf", "cour.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


def remove_foundry_background(image, tolerance: int = 35, green_screen: bool = True):
    """Foundry-style background removal: corner-color fallback plus green-screen key."""
    Image, _, _, _ = load_pillow()
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    bg = tuple(sum(pixel[channel] for pixel in corners) / len(corners) for channel in range(3))
    tol_sq = tolerance * tolerance

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            dist_sq = (red - bg[0]) ** 2 + (green - bg[1]) ** 2 + (blue - bg[2]) ** 2
            green_key = green_screen and green > 145 and green > red + 38 and green > blue + 38
            if dist_sq < tol_sq or green_key:
                pixels[x, y] = (red, green, blue, 0)
    return rgba


def foreground_bbox(image):
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    return alpha.getbbox()


def normalize_to_square(image, padding_ratio: float = 0.08):
    """Crop to foreground bounds, pad to square, preserve the full visible figure."""
    Image, _, _, _ = load_pillow()
    rgba = image.convert("RGBA")
    bbox = foreground_bbox(rgba)
    if bbox is None:
        side = max(rgba.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2), rgba)
        return square, None

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    pad = max(2, int(max(width, height) * padding_ratio))
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(rgba.width, right + pad)
    bottom = min(rgba.height, bottom + pad)
    cropped = rgba.crop((left, top, right, bottom))
    side = max(cropped.width, cropped.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2), cropped)
    return square, [left, top, right, bottom]


def pixelate_sprite_image(image, target_size: int, palette_colors: int | None = None):
    Image, _, _, _ = load_pillow()
    result = image.convert("RGBA").resize((target_size, target_size), Image.NEAREST)
    if palette_colors is not None and palette_colors > 0:
        alpha = result.getchannel("A")
        quantized = result.convert("RGB").quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT)
        result = quantized.convert("RGB").convert("RGBA")
        result.putalpha(alpha)
    return result


def raw_source_check(image, tolerance: int = 40) -> dict[str, Any]:
    """Small port of Foundry's raw source sanity check: empty frame and off-center content."""
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    corners = [
        pixels[0, 0],
        pixels[width - 1, 0],
        pixels[0, height - 1],
        pixels[width - 1, height - 1],
    ]
    bg = tuple(sum(pixel[channel] for pixel in corners) / len(corners) for channel in range(3))
    tol_sq = tolerance * tolerance
    total = 0
    sum_x = 0
    left_count = 0
    center_count = 0
    right_count = 0
    third = max(1, width // 3)

    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            dist_sq = (red - bg[0]) ** 2 + (green - bg[1]) ** 2 + (blue - bg[2]) ** 2
            if dist_sq <= tol_sq:
                continue
            total += 1
            sum_x += x
            if x < third:
                left_count += 1
            elif x < third * 2:
                center_count += 1
            else:
                right_count += 1

    if total == 0:
        return {"pass": False, "issues": ["empty_frame"]}

    issues: list[str] = []
    left_ratio = left_count / total
    right_ratio = right_count / total
    center_ratio = center_count / total
    if left_ratio > 0.25 and right_ratio > 0.25 and center_ratio < 0.35:
        issues.append("multi_subject_composition")

    center_of_mass = sum_x / total / width
    if center_of_mass < 0.30 or center_of_mass > 0.70:
        issues.append(f"off_center:{center_of_mass:.2f}")

    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "foreground_pixels": total,
        "center_of_mass_x": round(center_of_mass, 4),
    }


def mechanical_check_sprite(image, target_size: int) -> dict[str, Any]:
    issues: list[str] = []
    if image.size != (target_size, target_size):
        issues.append(f"wrong_size:{image.size}")
    if image.mode != "RGBA":
        issues.append(f"no_alpha:{image.mode}")
    else:
        max_index = target_size - 1
        corners = [
            image.getpixel((0, 0)),
            image.getpixel((max_index, 0)),
            image.getpixel((0, max_index)),
            image.getpixel((max_index, max_index)),
        ]
        opaque = sum(1 for corner in corners if corner[3] > 128)
        if opaque >= 3:
            issues.append("background_opaque")
    return {"pass": len(issues) == 0, "issues": issues}


def make_checkerboard(Image, ImageDraw, size: int, tile: int = 8):
    checker = Image.new("RGB", (size, size), (35, 35, 45))
    draw = ImageDraw.Draw(checker)
    for y in range(0, size, tile):
        for x in range(0, size, tile):
            color = (45, 45, 55) if (x // tile + y // tile) % 2 == 0 else (35, 35, 45)
            draw.rectangle([x, y, min(size - 1, x + tile - 1), min(size - 1, y + tile - 1)], fill=color)
    return checker


def write_pixel_contact_sheet(items: list[dict[str, Any]], target_path: Path, cell_size: int = 128) -> Path | None:
    pillow = load_pillow()
    if pillow is None:
        print("contact_sheet=skipped reason=Pillow-unavailable")
        return None
    Image, ImageDraw, ImageFont, _ = pillow
    by_direction = {str(item["direction"]): item for item in items if item.get("albedo_path")}
    if not by_direction:
        return None

    label_w = 88
    pad = 4
    header_h = 30
    cell_w = cell_size + pad * 2
    cell_h = cell_size + pad * 2
    width = label_w + len(ORDERED_DIRECTIONS) * cell_w + 20
    height = 10 + 24 + header_h + cell_h + 78
    sheet = Image.new("RGB", (width, height), (24, 24, 32))
    draw = ImageDraw.Draw(sheet)
    font_sm = load_default_font(ImageFont, 11)
    font_md = load_default_font(ImageFont, 13)
    font_lg = load_default_font(ImageFont, 15)

    ox, oy = 10, 10
    draw.text((ox, oy), "Nymphs Sprite - Foundry-style albedo contact sheet", fill=(120, 200, 120), font=font_lg)
    oy += 24
    for col, direction in enumerate(ORDERED_DIRECTIONS):
        draw.text((ox + label_w + col * cell_w + pad, oy + 2), direction.replace("_", "\n"), fill=(210, 210, 220), font=font_sm)
    oy += header_h
    draw.text((ox + 4, oy + cell_size // 2), "Albedo", fill=(120, 200, 120), font=font_md)
    for col, direction in enumerate(ORDERED_DIRECTIONS):
        cx = ox + label_w + col * cell_w + pad
        cy = oy + pad
        item = by_direction.get(direction)
        if item:
            with Image.open(Path(str(item["albedo_path"]))) as handle:
                sprite = handle.convert("RGBA").resize((cell_size, cell_size), Image.NEAREST)
            checker = make_checkerboard(Image, ImageDraw, cell_size)
            checker.paste(sprite, (0, 0), sprite)
            sheet.paste(checker, (cx, cy))
        else:
            draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(60, 30, 30), outline=(50, 50, 60))

    oy += cell_h + 10
    draw.line([(ox, oy), (width - 10, oy)], fill=(50, 50, 60))
    oy += 8
    draw.text((ox, oy), "Transparent sprite outputs, nearest-neighbor preview.", fill=(200, 200, 210), font=font_sm)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target_path)
    return target_path


def write_raw_inspection_sheet(items: list[dict[str, Any]], target_path: Path, cell_size: int = 192) -> Path | None:
    pillow = load_pillow()
    if pillow is None:
        return None
    Image, ImageDraw, ImageFont, ImageOps = pillow
    by_direction = {str(item["direction"]): item for item in items if item.get("raw_artifact_path")}
    if not by_direction:
        return None

    label_w = 92
    pad = 4
    header_h = 30
    cell_w = cell_size + pad * 2
    cell_h = cell_size + pad * 2
    width = label_w + len(ORDERED_DIRECTIONS) * cell_w + 20
    height = 10 + 24 + header_h + cell_h + 78
    sheet = Image.new("RGB", (width, height), (24, 24, 32))
    draw = ImageDraw.Draw(sheet)
    font_sm = load_default_font(ImageFont, 11)
    font_md = load_default_font(ImageFont, 13)
    font_lg = load_default_font(ImageFont, 15)

    ox, oy = 10, 10
    draw.text((ox, oy), "Nymphs Sprite - raw source inspection", fill=(200, 120, 120), font=font_lg)
    oy += 24
    for col, direction in enumerate(ORDERED_DIRECTIONS):
        draw.text((ox + label_w + col * cell_w + pad, oy + 2), direction.replace("_", "\n"), fill=(210, 210, 220), font=font_sm)
    oy += header_h
    draw.text((ox + 2, oy + cell_size // 2 - 8), "Raw", fill=(200, 120, 120), font=font_md)
    for col, direction in enumerate(ORDERED_DIRECTIONS):
        cx = ox + label_w + col * cell_w + pad
        cy = oy + pad
        item = by_direction.get(direction)
        if item:
            with Image.open(Path(str(item["raw_artifact_path"]))) as handle:
                thumb = ImageOps.contain(handle.convert("RGB"), (cell_size, cell_size))
            px = cx + (cell_size - thumb.width) // 2
            py = cy + (cell_size - thumb.height) // 2
            sheet.paste(thumb, (px, py))
        else:
            draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(60, 30, 30), outline=(50, 50, 60))

    oy += cell_h + 10
    draw.line([(ox, oy), (width - 10, oy)], fill=(50, 50, 60))
    oy += 8
    draw.text((ox, oy), "Check identity, single subject, centering, and background residue before accepting.", fill=(200, 200, 210), font=font_sm)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target_path)
    return target_path


def process_foundry_sprite(source: Path, batch_dir: Path, item: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    result: dict[str, Any] = {
        "raw_artifact_path": "",
        "albedo_path": "",
        "preview_path": "",
        "crop_bbox": None,
        "source_check": {"pass": False, "issues": ["not_processed"]},
        "mechanical": {"pass": False, "issues": ["not_processed"]},
    }
    if not source.exists() or not source.is_file():
        result["source_check"] = {"pass": False, "issues": ["source_missing"]}
        result["mechanical"] = {"pass": False, "issues": ["source_missing"]}
        return result

    raw_path = copy_direction_image(source, batch_dir / "raw", int(item["index"]), str(item["direction"]), "_raw")
    if raw_path is not None:
        result["raw_artifact_path"] = str(raw_path)

    pillow = load_pillow()
    if pillow is None:
        result["source_check"] = {"pass": False, "issues": ["Pillow-unavailable"]}
        result["mechanical"] = {"pass": False, "issues": ["Pillow-unavailable"]}
        return result

    Image, _, _, _ = pillow
    with Image.open(source) as handle:
        raw_img = handle.convert("RGBA")

    source_check = raw_source_check(raw_img)
    cleaned = remove_foundry_background(raw_img, tolerance=args.bg_tolerance, green_screen=not args.no_green_screen)
    square, bbox = normalize_to_square(cleaned, padding_ratio=args.crop_padding)
    pixel = pixelate_sprite_image(square, args.sprite_size, args.palette_colors)
    mechanical = mechanical_check_sprite(pixel, args.sprite_size)

    albedo_path = batch_dir / "albedo" / f"{int(item['index']):02d}_{item['direction']}.png"
    albedo_path.parent.mkdir(parents=True, exist_ok=True)
    pixel.save(albedo_path, "PNG")

    preview_size = max(args.sprite_size, args.preview_size)
    preview = pixel.resize((preview_size, preview_size), Image.NEAREST)
    preview_path = batch_dir / "preview" / f"{int(item['index']):02d}_{item['direction']}_preview.png"
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    preview.save(preview_path, "PNG")

    result.update(
        {
            "albedo_path": str(albedo_path),
            "preview_path": str(preview_path),
            "crop_bbox": bbox,
            "source_check": source_check,
            "mechanical": mechanical,
        }
    )
    return result


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
        processed: dict[str, Any] = {}
        if source is not None and args.copy_images:
            artifact_path = copy_direction_image(source, directions_dir, int(item["index"]), str(item["direction"]))
        if source is not None and args.post_process:
            processed = process_foundry_sprite(source, batch_dir, item, args)
        copied_items.append(
            {
                "direction": item["direction"],
                "index": item["index"],
                "seed": item["seed"],
                "prompt": item["prompt"],
                "generation_mode": item.get("mode", "txt2img"),
                "control_source_path": item.get("control_source_path", ""),
                "source_output_path": str(source) if source else "",
                "source_metadata_path": str(response.get("metadata_path") or ""),
                "source_url": str(response.get("url") or ""),
                "artifact_path": str(artifact_path) if artifact_path else "",
                "raw_artifact_path": processed.get("raw_artifact_path", ""),
                "albedo_path": processed.get("albedo_path", ""),
                "preview_path": processed.get("preview_path", ""),
                "crop_bbox": processed.get("crop_bbox"),
                "source_check": processed.get("source_check", {}),
                "mechanical": processed.get("mechanical", {}),
                "zimage_response": response,
            }
        )

    contact_sheet = write_pixel_contact_sheet(copied_items, batch_dir / "preview" / "contact_sheet.png", args.contact_cell_size)
    raw_sheet = write_raw_inspection_sheet(copied_items, batch_dir / "preview" / "raw_inspection.png", args.raw_cell_size)
    processed_count = sum(1 for item in copied_items if item.get("albedo_path"))
    mechanical_passes = sum(1 for item in copied_items if (item.get("mechanical") or {}).get("pass") is True)
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
        "sprite_size": args.sprite_size,
        "post_process": args.post_process,
        "source_mode": args.source_mode,
        "controlnet_conditioning_scale": args.controlnet_scale if args.source_mode == "controlnet" else None,
        "processed_count": processed_count,
        "mechanical_passes": mechanical_passes,
        "directions": copied_items,
        "contact_sheet": str(contact_sheet) if contact_sheet else "",
        "raw_inspection": str(raw_sheet) if raw_sheet else "",
    }
    batch_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = batch_dir / "sprite_batch.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "batch_dir": str(batch_dir),
        "manifest_path": str(manifest_path),
        "contact_sheet": str(contact_sheet) if contact_sheet else "",
        "raw_inspection": str(raw_sheet) if raw_sheet else "",
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
    parser.add_argument("--lora-scale", type=float, default=1.0)
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
    parser.add_argument("--source-images", default="")
    parser.add_argument("--source-mode", choices=["process", "controlnet"], default="process")
    parser.add_argument("--controlnet-scale", type=float, default=0.55)
    parser.add_argument("--contact-cell-size", type=int, default=192)
    parser.add_argument("--raw-cell-size", type=int, default=192)
    parser.add_argument("--preview-size", type=int, default=192)
    parser.add_argument("--sprite-size", type=int, default=96)
    parser.add_argument("--bg-tolerance", type=int, default=35)
    parser.add_argument("--crop-padding", type=float, default=0.08)
    parser.add_argument("--palette-colors", type=int, default=0)
    parser.add_argument("--copy-images", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--post-process", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--green-screen", dest="no_green_screen", action="store_false", default=False)
    parser.add_argument("--no-green-screen", dest="no_green_screen", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.sprite_size < 24 or args.sprite_size > 512:
        raise SystemExit("ERROR: --sprite-size must be between 24 and 512.")
    if args.palette_colors < 0:
        raise SystemExit("ERROR: --palette-colors must be zero or greater.")
    if args.crop_padding < 0 or args.crop_padding > 0.5:
        raise SystemExit("ERROR: --crop-padding must be between 0 and 0.5.")
    zimage_url = args.zimage_url.rstrip("/")
    profile = {}
    if args.profile:
        profile = load_profile(Path(args.profile).expanduser())

    source_images = split_source_images(args.source_images)
    batch_id = f"nymphs-sprite-{args.subject_id}-{uuid.uuid4().hex[:8]}"
    direction_names = [item.strip() for item in re.split(r"[,+]", args.directions) if item.strip()]
    invalid = [name for name in direction_names if name not in DIRECTIONS]
    if invalid:
        raise SystemExit(f"ERROR: unknown direction(s): {', '.join(invalid)}")
    if args.controlnet_scale <= 0 or args.controlnet_scale > 2:
        raise SystemExit("ERROR: --controlnet-scale must be greater than 0 and <= 2.")

    if source_images:
        missing = [str(path) for path in source_images if not path.is_file()]
        if missing:
            raise SystemExit(f"ERROR: selected source image(s) not found: {', '.join(missing)}")
        print(f"batch_id={batch_id}", flush=True)
        print(f"source_images={len(source_images)}", flush=True)
        print(f"source_mode={args.source_mode}", flush=True)
        if args.source_mode == "process":
            generated = []
            for index, source in enumerate(source_images, start=1):
                direction = source_direction_name(source, index)
                generated.append(
                    {
                        "direction": direction,
                        "index": index,
                        "seed": args.seed + (index - 1) * args.seed_step,
                        "prompt": args.subject_prompt,
                        "response": {"output_path": str(source), "url": "", "metadata_path": ""},
                    }
                )
                print(f"output_{direction}={source}", flush=True)
            artifacts = write_sprite_artifacts(
                outputs_root=Path(args.outputs_root),
                subject_id=args.subject_id,
                batch_id=batch_id,
                lora_path=args.lora_path.strip() or str(profile.get("lora_path") or "").strip(),
                lora_trigger=args.lora_trigger.strip() or str(profile.get("lora_trigger") or "").strip(),
                args=args,
                generated=generated,
            )
            print(f"sprite_batch_dir={artifacts['batch_dir']}", flush=True)
            print(f"sprite_manifest={artifacts['manifest_path']}", flush=True)
            if artifacts["contact_sheet"]:
                print(f"sprite_contact_sheet={artifacts['contact_sheet']}", flush=True)
            print(json.dumps({"status": "ok", "batch_id": batch_id, "outputs": [], "artifacts": artifacts}, indent=2), flush=True)
            return 0

    lora_path = args.lora_path.strip() or str(profile.get("lora_path") or "").strip()
    if not lora_path:
        lora_path = latest_lora_path(zimage_url) or ""
    if not lora_path:
        raise SystemExit("ERROR: no LoRA path supplied and /api/loras returned no available LoRAs.")

    lora_trigger = args.lora_trigger.strip() or str(profile.get("lora_trigger") or "").strip()
    control_sources = control_sources_by_direction(source_images, direction_names) if source_images and args.source_mode == "controlnet" else {}

    print(f"batch_id={batch_id}", flush=True)
    print(f"lora_path={lora_path}", flush=True)
    ensure_zimage_model_loaded(zimage_url, args)

    outputs = []
    generated = []
    for index, direction in enumerate(direction_names, start=1):
        prompt_parts = [
            lora_trigger,
            args.subject_prompt,
            DIRECTIONS[direction],
            STYLE_SUFFIX,
        ]
        prompt = ", ".join(part for part in prompt_parts if part)
        control_source = control_sources.get(direction)
        payload = {
            "provider": "zimage",
            "mode": "controlnet_edit" if control_source is not None else "txt2img",
            "model_id": "Tongyi-MAI/Z-Image-Turbo",
            "nunchaku_rank": args.nunchaku_rank,
            "nunchaku_precision": args.nunchaku_precision,
            "width": args.width,
            "height": args.height,
            "steps": args.steps,
            "guidance_scale": args.guidance_scale,
            "seed": args.seed + (index - 1) * args.seed_step,
            "prompt": prompt,
            "negative_prompt": foundry_negative_prompt(args.negative_prompt),
            "lora_path": lora_path,
            "lora_scale": args.lora_scale,
            "batch_id": batch_id,
            "batch_label": f"Nymphs Sprite: {args.subject_id}",
            "batch_type": "sprite_direction",
            "item_label": direction,
            "item_index": index,
            "item_total": len(direction_names),
        }
        if control_source is not None:
            payload["image"] = image_data_url(control_source)
            payload["controlnet_conditioning_scale"] = args.controlnet_scale
            print(f"controlnet_{direction}={control_source} scale={args.controlnet_scale}", flush=True)
        print(f"generate={direction} seed={payload['seed']}", flush=True)
        response = request_json("POST", f"{zimage_url.rstrip('/')}/generate", payload=payload)
        outputs.append(response)
        generated.append(
            {
                "direction": direction,
                "index": index,
                "seed": payload["seed"],
                "prompt": prompt,
                "mode": payload["mode"],
                "control_source_path": str(control_source) if control_source is not None else "",
                "response": response,
            }
        )
        print(f"output_{direction}={response.get('output_path')}", flush=True)
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
    print(f"sprite_batch_dir={artifacts['batch_dir']}", flush=True)
    print(f"sprite_manifest={artifacts['manifest_path']}", flush=True)
    if artifacts["contact_sheet"]:
        print(f"sprite_contact_sheet={artifacts['contact_sheet']}", flush=True)

    print(json.dumps({"status": "ok", "batch_id": batch_id, "outputs": outputs, "artifacts": artifacts}, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
