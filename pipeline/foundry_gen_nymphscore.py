"""Nymphs Sprite integrated NymphsCore/Nymphs Image generation runner.

This preserves the inherited review, mechanical gates, maps, finish, and export
contracts while replacing the ComfyUI prompt queue with Nymphs Image's Z-Image
`/generate` API.

Usage:
    python -m pipeline.foundry_gen_nymphscore --config pipeline/chars/thal.json
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from foundry import db
from pipeline.nymphscore_client import generate_zimage, output_path


FOUNDRY_ROOT = Path(__file__).parent.parent
DEFAULT_NYMPHSCORE_URL = "http://127.0.0.1:8090"
DEFAULT_MODEL_ID = "Tongyi-MAI/Z-Image-Turbo"

DIRECTIONS_8 = [
    ("front", "facing the viewer, front view, looking at camera"),
    ("front_left", "facing front-left, 3/4 view from the left, looking slightly left"),
    ("left", "facing left, left side profile view"),
    ("back_left", "facing back-left, 3/4 rear view from the left"),
    ("back", "facing away from viewer, rear view, back of character"),
    ("back_right", "facing back-right, 3/4 rear view from the right"),
    ("right", "facing right, right side profile view"),
    ("front_right", "facing front-right, 3/4 view from the right, looking slightly right"),
]
DIRECTIONS_16 = [
    ("front", "facing the viewer, front view, looking at camera"),
    ("front_front_left", "facing slightly front-left, subtle 1/16 turn from front"),
    ("front_left", "facing front-left, 3/4 view from the left, looking slightly left"),
    ("left_front_left", "facing between front-left and left side profile"),
    ("left", "facing left, left side profile view"),
    ("left_back_left", "facing between left side profile and back-left"),
    ("back_left", "facing back-left, 3/4 rear view from the left"),
    ("back_back_left", "facing slightly back-left, subtle 1/16 turn from back"),
    ("back", "facing away from viewer, rear view, back of character"),
    ("back_back_right", "facing slightly back-right, subtle 1/16 turn from back"),
    ("back_right", "facing back-right, 3/4 rear view from the right"),
    ("right_back_right", "facing between right side profile and back-right"),
    ("right", "facing right, right side profile view"),
    ("right_front_right", "facing between front-right and right side profile"),
    ("front_right", "facing front-right, 3/4 view from the right, looking slightly right"),
    ("front_front_right", "facing slightly front-right, subtle 1/16 turn from front"),
]
DIRECTIONS = DIRECTIONS_8

STYLE_SUFFIX = (
    "pixel art sprite, game character sprite, 2D RPG, clean readable silhouette, "
    "centered full body character, isolated figure, bright green background, "
    "crisp sprite design, HD-2D inspired, single character only"
)

NEGATIVE_BG = "white background, gray background, grey background, beige background, gradient background"
POSE_CONTROL_PROMPT = (
    "mandatory Pose Lab control reference, match the supplied control reference for body pose, "
    "limb placement, stance, silhouette, and direction, do not invent a different pose"
)
POSE_CONTROL_NEGATIVE = (
    "pose that does not match the control reference, limbs that do not match the control reference, "
    "different stance than the control reference"
)
POSE_CONFLICT_PATTERN = re.compile(
    r"\b("
    r"pose|posture|stance|standing|stand|stands|crouch|crouched|crouching|hunch|hunched|"
    r"leaning|forward lean|backward lean|weight on|ready to spring|ready-to-spring|"
    r"lowest|horizontal profile|sneaking|ambush|predator|lumbering|hovering|floating|"
    r"arms?|hands?|legs?|feet|foot|knees?|ankles?|wrist|elbow|shoulder|"
    r"holding|held|gripping|raised|overhead|at sides?|profile view|side view|front view|rear view|"
    r"looking at camera|looking left|looking right|facing"
    r")\b",
    re.IGNORECASE,
)

POSE_JOINTS = [
    "head", "neck", "spine", "pelvis",
    "left_shoulder", "left_elbow", "left_wrist",
    "right_shoulder", "right_elbow", "right_wrist",
    "left_hip", "left_knee", "left_ankle",
    "right_hip", "right_knee", "right_ankle",
]

POSE_SEGMENTS = [
    ("head", "neck", (255, 0, 190)),
    ("neck", "spine", (0, 210, 230)),
    ("spine", "pelvis", (0, 210, 230)),
    ("neck", "left_shoulder", (255, 156, 0)),
    ("left_shoulder", "left_elbow", (255, 156, 0)),
    ("left_elbow", "left_wrist", (255, 156, 0)),
    ("neck", "right_shoulder", (0, 220, 65)),
    ("right_shoulder", "right_elbow", (0, 220, 65)),
    ("right_elbow", "right_wrist", (0, 220, 65)),
    ("pelvis", "left_hip", (0, 190, 125)),
    ("left_hip", "left_knee", (0, 190, 125)),
    ("left_knee", "left_ankle", (0, 190, 125)),
    ("pelvis", "right_hip", (0, 80, 230)),
    ("right_hip", "right_knee", (0, 80, 230)),
    ("right_knee", "right_ankle", (0, 80, 230)),
]


def foundry_cmd(*args: str) -> int:
    cmd = [sys.executable, "-m", "foundry.cli"] + list(args)
    result = subprocess.run(cmd, cwd=str(FOUNDRY_ROOT), capture_output=True, text=True)
    if result.stdout:
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and result.stderr:
        print(f"    ERROR: {result.stderr.strip()}")
    return result.returncode


def ensure_subject(config: dict[str, Any]) -> None:
    conn = db.init_db()
    subject_id = config["subject_id"]
    existing = conn.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    if not existing:
        conn.execute(
            """INSERT INTO subjects (id, display_name, role, consumer, subject_sheet_path, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                subject_id,
                config.get("display_name") or subject_id,
                config.get("role") or "sprite",
                config.get("consumer") or "nymphscore",
                config.get("subject_sheet_path"),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        print(f"  Registered subject: {subject_id}")
    conn.close()


def remove_bg(image: Image.Image, tolerance: int = 35, green_screen: bool = True) -> Image.Image:
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


def normalize_to_square(image: Image.Image, padding_ratio: float = 0.08) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        side = max(rgba.size)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2), rgba)
        return square

    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    pad = max(2, int(max(width, height) * padding_ratio))
    cropped = rgba.crop(
        (
            max(0, left - pad),
            max(0, top - pad),
            min(rgba.width, right + pad),
            min(rgba.height, bottom + pad),
        )
    )
    side = max(cropped.width, cropped.height)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(cropped, ((side - cropped.width) // 2, (side - cropped.height) // 2), cropped)
    return square


def pixelate(image: Image.Image, sprite_size: int, palette_colors: int = 0) -> Image.Image:
    result = image.convert("RGBA").resize((sprite_size, sprite_size), Image.NEAREST)
    if palette_colors > 0:
        alpha = result.getchannel("A")
        quantized = result.convert("RGB").quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT)
        result = quantized.convert("RGB").convert("RGBA")
        result.putalpha(alpha)
    return result


def guide_strength_scale(value: str) -> float:
    return {
        "soft": 0.75,
        "normal": 0.90,
        "strong": 1.00,
    }.get(str(value or "normal").strip().lower(), 0.90)


def latest_pose_lab_set(subject_id: str, direction_count: int) -> tuple[Path, dict[str, Any]] | None:
    root = Path.home() / "NymphsData" / "outputs" / "nymphs-sprite" / "pose_lab" / "refs" / subject_id
    if not root.is_dir():
        return None
    candidates = sorted(root.glob("*/pose_set.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if int(data.get("direction_count") or 0) not in {0, direction_count}:
            continue
        directions = data.get("pose_data", {}).get("directions", {})
        if isinstance(directions, dict) and directions:
            return path, data
    return None


def pose_points(slot: dict[str, Any]) -> dict[str, tuple[float, float]]:
    joints = slot.get("joints") if isinstance(slot, dict) else None
    if not isinstance(joints, dict):
        return {}
    points: dict[str, tuple[float, float]] = {}
    for name in POSE_JOINTS:
        raw = joints.get(name)
        if not isinstance(raw, list | tuple) or len(raw) < 2:
            continue
        try:
            points[name] = (float(raw[0]), float(raw[1]))
        except (TypeError, ValueError):
            continue
    return points


def render_pose_control_data_url(slot: dict[str, Any], width: int, height: int, canvas_size: float = 256) -> str | None:
    points = pose_points(slot)
    if len(points) < 8:
        return None
    canvas_size = canvas_size if canvas_size > 0 else 256
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)

    def transform(point: tuple[float, float]) -> tuple[float, float]:
        x = max(0.0, min(canvas_size, point[0])) / canvas_size * width
        y = max(0.0, min(canvas_size, point[1])) / canvas_size * height
        return x, y

    line_width = max(4, int(round(min(width, height) * 0.008)))
    dot_radius = max(4, int(round(min(width, height) * 0.008)))
    for a, b, color in POSE_SEGMENTS:
        if a not in points or b not in points:
            continue
        draw.line([transform(points[a]), transform(points[b])], fill=color, width=line_width)
    for index, name in enumerate(POSE_JOINTS):
        if name not in points:
            continue
        x, y = transform(points[name])
        fill = (255, 0, 210) if index % 3 == 0 else (245, 255, 0)
        draw.ellipse([x - dot_radius, y - dot_radius, x + dot_radius, y + dot_radius], fill=fill)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def save_data_url_png(data_url: str, path: Path) -> None:
    marker = "base64,"
    if marker not in data_url:
        return
    try:
        raw = base64.b64decode(data_url.split(marker, 1)[1])
    except Exception:
        return
    path.write_bytes(raw)


def image_file_data_url(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def pose_safe_text(text: str) -> str:
    clauses = [clause.strip() for clause in str(text or "").split(",")]
    kept = [clause for clause in clauses if clause and not POSE_CONFLICT_PATTERN.search(clause)]
    return ", ".join(kept)


def checkerboard(size: int, tile: int = 8) -> Image.Image:
    image = Image.new("RGB", (size, size), (35, 35, 45))
    draw = ImageDraw.Draw(image)
    for y in range(0, size, tile):
        for x in range(0, size, tile):
            color = (45, 45, 55) if (x // tile + y // tile) % 2 == 0 else (35, 35, 45)
            draw.rectangle([x, y, min(size - 1, x + tile - 1), min(size - 1, y + tile - 1)], fill=color)
    return image


def font(size: int):
    for name in ("consola.ttf", "cour.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            pass
    return ImageFont.load_default()


def make_contact_sheets(
    raw_paths: dict[str, Path],
    pixel_paths: dict[str, Path],
    *,
    directions: list[tuple[str, str]],
    display_name: str,
    stack: str,
    sprite_size: int,
    final_label: str,
    out_dir: Path,
    raw_cell_size: int,
    preview_cell_size: int,
) -> tuple[Path, Path]:
    label_w = 92
    pad = 4
    header_h = 30
    text = (210, 210, 220)
    grid = (50, 50, 60)
    bg = (24, 24, 32)
    direction_names = [name for name, _ in directions]

    raw_w = label_w + len(direction_names) * (raw_cell_size + pad * 2) + 20
    raw_h = 10 + 24 + header_h + raw_cell_size + pad * 2 + 78
    raw_sheet = Image.new("RGB", (raw_w, raw_h), bg)
    draw = ImageDraw.Draw(raw_sheet)
    ox, oy = 10, 10
    draw.text((ox, oy), f"RAW SOURCE INSPECTION -- {display_name} -- {stack}", fill=(200, 120, 120), font=font(15))
    oy += 24
    for col, name in enumerate(direction_names):
        draw.text((ox + label_w + col * (raw_cell_size + pad * 2) + pad, oy + 2), name.replace("_", "\n"), fill=text, font=font(11))
    oy += header_h
    draw.text((ox + 2, oy + raw_cell_size // 2 - 8), "Raw", fill=(200, 120, 120), font=font(13))
    for col, name in enumerate(direction_names):
        cx = ox + label_w + col * (raw_cell_size + pad * 2) + pad
        cy = oy + pad
        if name in raw_paths:
            with Image.open(raw_paths[name]) as handle:
                thumb = ImageOps.contain(handle.convert("RGB"), (raw_cell_size, raw_cell_size))
            raw_sheet.paste(thumb, (cx + (raw_cell_size - thumb.width) // 2, cy + (raw_cell_size - thumb.height) // 2))
        else:
            draw.rectangle([cx, cy, cx + raw_cell_size, cy + raw_cell_size], fill=(60, 30, 30), outline=grid)
    raw_path = out_dir / "raw_inspection.png"
    raw_sheet.save(raw_path)

    pixel_w = 80 + len(direction_names) * (preview_cell_size + pad * 2) + 20
    pixel_h = 10 + 24 + header_h + preview_cell_size + pad * 2 + 78
    pixel_sheet = Image.new("RGB", (pixel_w, pixel_h), bg)
    draw = ImageDraw.Draw(pixel_sheet)
    ox, oy = 10, 10
    draw.text((ox, oy), f"{display_name} -- {stack} ({final_label})", fill=(120, 200, 120), font=font(15))
    oy += 24
    for col, name in enumerate(direction_names):
        draw.text((ox + 80 + col * (preview_cell_size + pad * 2) + pad, oy + 2), name.replace("_", "\n"), fill=text, font=font(11))
    oy += header_h
    for col, name in enumerate(direction_names):
        cx = ox + 80 + col * (preview_cell_size + pad * 2) + pad
        cy = oy + pad
        if name in pixel_paths:
            with Image.open(pixel_paths[name]) as handle:
                sprite = handle.convert("RGBA").resize((preview_cell_size, preview_cell_size), Image.NEAREST)
            board = checkerboard(preview_cell_size)
            board.paste(sprite, (0, 0), sprite)
            pixel_sheet.paste(board, (cx, cy))
        else:
            draw.rectangle([cx, cy, cx + preview_cell_size, cy + preview_cell_size], fill=(60, 30, 30), outline=grid)
    pixel_path = out_dir / "contact_sheet.png"
    pixel_sheet.save(pixel_path)
    return raw_path, pixel_path


def build_payload(
    *,
    args: argparse.Namespace,
    batch_id: str,
    backend_dir: Path,
    direction_name: str,
    direction_prompt: str,
    index: int,
    direction_count: int,
    config: dict[str, Any],
    lora_path: str,
    seed: int,
    control_image: str | None = None,
    controlnet_scale: float = 0.75,
    controlnet_guidance_scale: float | None = None,
) -> dict[str, Any]:
    pose_control_active = bool(control_image)
    subject_prompt = str(config["subject_prompt"])
    negative = str(config.get("negative_prompt") or "")
    if pose_control_active:
        subject_prompt = pose_safe_text(subject_prompt)
        negative = pose_safe_text(negative)
    full_negative = f"{negative}, {NEGATIVE_BG}" if negative else NEGATIVE_BG
    if pose_control_active:
        full_negative = f"{full_negative}, {POSE_CONTROL_NEGATIVE}"
    effective_lora_path = lora_path
    effective_lora_scale = args.lora_scale
    if control_image and getattr(args, "controlnet_lora_mode", "on") != "on":
        effective_lora_path = ""
        effective_lora_scale = None
    prompt_parts = [
        args.lora_trigger if effective_lora_path else "",
        subject_prompt,
        POSE_CONTROL_PROMPT if pose_control_active else "",
        direction_prompt,
        STYLE_SUFFIX,
    ]
    payload = {
        "provider": "zimage",
        "mode": "txt2img",
        "model_id": args.model_id,
        "nunchaku_rank": args.nunchaku_rank,
        "nunchaku_precision": args.nunchaku_precision,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "seed": seed,
        "prompt": ", ".join(part for part in prompt_parts if part),
        "negative_prompt": full_negative,
        "lora_path": effective_lora_path,
        "lora_scale": effective_lora_scale,
        "batch_id": batch_id,
        "batch_label": f"Nymphs Sprite: {config.get('display_name') or config['subject_id']}",
        "batch_type": "sprite_foundry_direction",
        "item_label": direction_name,
        "item_index": index,
        "item_total": direction_count,
        "output_dir": str(backend_dir),
    }
    if control_image:
        payload["mode"] = "controlnet_edit"
        payload["image"] = control_image
        payload["controlnet_conditioning_scale"] = controlnet_scale
        if controlnet_guidance_scale is not None:
            payload["guidance_scale"] = controlnet_guidance_scale
    return payload


def build_lora_img2img_payload(
    *,
    args: argparse.Namespace,
    batch_id: str,
    backend_dir: Path,
    direction_name: str,
    direction_prompt: str,
    index: int,
    direction_count: int,
    config: dict[str, Any],
    lora_path: str,
    seed: int,
    image_path: Path,
) -> dict[str, Any]:
    subject_prompt = pose_safe_text(str(config["subject_prompt"]))
    negative = pose_safe_text(str(config.get("negative_prompt") or ""))
    full_negative = f"{negative}, {NEGATIVE_BG}" if negative else NEGATIVE_BG
    prompt_parts = [
        args.lora_trigger if lora_path else "",
        subject_prompt,
        "preserve the input image pose, silhouette, direction, and centered full body framing",
        direction_prompt,
        STYLE_SUFFIX,
    ]
    return {
        "provider": "zimage",
        "mode": "img2img",
        "model_id": args.model_id,
        "nunchaku_rank": args.nunchaku_rank,
        "nunchaku_precision": args.nunchaku_precision,
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "strength": args.lora_img2img_strength,
        "seed": seed,
        "image": image_file_data_url(image_path),
        "prompt": ", ".join(part for part in prompt_parts if part),
        "negative_prompt": full_negative,
        "lora_path": lora_path,
        "lora_scale": args.lora_scale,
        "batch_id": batch_id,
        "batch_label": f"Nymphs Sprite: {config.get('display_name') or config['subject_id']}",
        "batch_type": "sprite_foundry_direction_lora_refine",
        "item_label": f"{direction_name}_lora_refine",
        "item_index": index,
        "item_total": direction_count,
        "output_dir": str(backend_dir),
    }


def selected_directions(args: argparse.Namespace) -> list[tuple[str, str]]:
    directions = DIRECTIONS_16 if int(args.direction_count) == 16 else DIRECTIONS_8
    max_directions = int(getattr(args, "max_directions", 0) or 0)
    if max_directions > 0:
        return directions[:max_directions]
    return directions


def clean_backend_staging(root: Path) -> None:
    if root.name != "_backend":
        return
    if not root.is_dir():
        return
    for child in root.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        elif child.is_file():
            child.unlink(missing_ok=True)


def generate_and_register(config: dict[str, Any], args: argparse.Namespace) -> str:
    if args.sprite_size < 24 or args.sprite_size > 512:
        raise SystemExit("--sprite-size must be between 24 and 512")
    if args.palette_colors < 0:
        raise SystemExit("--palette-colors must be zero or greater")
    if args.direction_count not in (8, 16):
        raise SystemExit("--direction-count must be 8 or 16")

    ensure_subject(config)
    directions = selected_directions(args)

    subject_id = config["subject_id"]
    display_name = config.get("display_name") or subject_id
    seed = args.seed if args.seed is not None else int(config["seed"])
    lora_path = "" if getattr(args, "debug_no_lora", False) else args.lora_path
    if not lora_path and not getattr(args, "debug_no_lora", False):
        raise SystemExit("No LoRA path supplied. Choose a Nymphs Sprite LoRA in the UI before generating.")
    pose_set = latest_pose_lab_set(subject_id, len(directions))
    pose_set_path: Path | None = None
    pose_directions: dict[str, Any] = {}
    pose_canvas_size = 256.0
    if pose_set:
        pose_set_path, pose_set_data = pose_set
        pose_data = pose_set_data.get("pose_data") if isinstance(pose_set_data.get("pose_data"), dict) else {}
        pose_directions = pose_data.get("directions") if isinstance(pose_data.get("directions"), dict) else {}
        try:
            pose_canvas_size = float(pose_data.get("canvas_size") or 256)
        except (TypeError, ValueError):
            pose_canvas_size = 256.0

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"{subject_id}_nymphscore_{ts}"
    out_dir = Path.home() / "NymphsData" / "outputs" / "nymphs-sprite" / subject_id
    backend_root = Path.home() / "NymphsData" / "outputs" / "nymphs-sprite" / "_backend"
    clean_backend_staging(backend_root)
    backend_dir = backend_root / run_id
    intermediate_dir = out_dir / "_intermediate"
    out_dir.mkdir(parents=True, exist_ok=True)
    backend_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    all_direction_names = {name for name, _ in DIRECTIONS_8 + DIRECTIONS_16}
    for direction_name in all_direction_names:
        for suffix in (".png", "_raw.png", "_raw.json"):
            (out_dir / f"{direction_name}{suffix}").unlink(missing_ok=True)
        (intermediate_dir / f"{direction_name}_cutout.png").unlink(missing_ok=True)
    for filename in ("raw_inspection.png", "contact_sheet.png", "recipe.json", "manifest.json"):
        (out_dir / filename).unlink(missing_ok=True)

    print(f"\n{'=' * 60}")
    print(f"NYMPHSCORE GENERATION: {display_name}")
    print(f"Run: {run_id}  Seed: {seed}")
    print(f"Output: {out_dir}")
    print(f"Nymphs Image: {args.nymphscore_url}")
    print(f"Directions: {len(directions)}")
    if pose_set_path:
        print(f"Pose Lab refs: {pose_set_path}")
    else:
        print("Pose Lab refs: none found; using text-only direction prompts.")
    print(f"{'=' * 60}\n")

    raw_paths: dict[str, Path] = {}
    cutout_paths: dict[str, Path] = {}
    pixel_paths: dict[str, Path] = {}
    generated_dirs: list[str] = []
    responses: dict[str, Any] = {}
    direction_seeds: dict[str, int] = {}
    controlnet_used: list[str] = []
    controlnet_lora_bypassed: list[str] = []
    lora_stage2_used: list[str] = []
    controlnet_scale = guide_strength_scale(args.guide_strength)
    controlnet_guidance_scale = getattr(args, "controlnet_guidance_scale", 0.0)
    controlnet_lora_mode = getattr(args, "controlnet_lora_mode", "on")
    postprocess_output = not bool(getattr(args, "no_postprocess", False))
    pixelate_output = not bool(getattr(args, "no_pixelate", False))
    if not postprocess_output:
        pixelate_output = False

    for index, (direction_name, direction_prompt) in enumerate(directions, start=1):
        item_seed = seed + (index - 1) * args.seed_step
        pose_slot = pose_directions.get(direction_name) if isinstance(pose_directions, dict) else None
        control_image = None
        if getattr(args, "controlnet_mode", "auto") != "off" and isinstance(pose_slot, dict):
            control_image = render_pose_control_data_url(pose_slot, args.width, args.height, pose_canvas_size)
        mode_label = "controlnet" if control_image else "txt2img"
        print(f"  [{direction_name}] generate seed={item_seed} mode={mode_label}...", end=" ", flush=True)
        if control_image:
            save_data_url_png(control_image, out_dir / f"{direction_name}_control.png")
            if lora_path and controlnet_lora_mode != "on":
                controlnet_lora_bypassed.append(direction_name)
        payload = build_payload(
            args=args,
            batch_id=run_id,
            backend_dir=backend_dir,
            direction_name=direction_name,
            direction_prompt=direction_prompt,
            index=index,
            direction_count=len(directions),
            config=config,
            lora_path=lora_path,
            seed=item_seed,
            control_image=control_image,
            controlnet_scale=controlnet_scale,
            controlnet_guidance_scale=controlnet_guidance_scale,
        )
        try:
            response = generate_zimage(args.nymphscore_url, payload)
            source = output_path(response)
            if source is None or not source.exists():
                raise RuntimeError(f"missing output_path in response: {response}")
            if control_image and lora_path and controlnet_lora_mode == "staged":
                pose_raw_path = out_dir / f"{direction_name}_pose_raw.png"
                pose_metadata = source.with_suffix(".json")
                shutil.move(str(source), str(pose_raw_path))
                if pose_metadata.is_file():
                    shutil.move(str(pose_metadata), str(pose_raw_path.with_suffix(".json")))
                lora_payload = build_lora_img2img_payload(
                    args=args,
                    batch_id=run_id,
                    backend_dir=backend_dir,
                    direction_name=direction_name,
                    direction_prompt=direction_prompt,
                    index=index,
                    direction_count=len(directions),
                    config=config,
                    lora_path=lora_path,
                    seed=item_seed,
                    image_path=pose_raw_path,
                )
                response = generate_zimage(args.nymphscore_url, lora_payload)
                source = output_path(response)
                if source is None or not source.exists():
                    raise RuntimeError(f"missing lora refine output_path in response: {response}")
                lora_stage2_used.append(direction_name)
        except Exception as exc:
            message = str(exc)
            print(f"FAIL: {message}")
            if "No Z-Image LoRA weights matched" in message:
                raise SystemExit(
                    "Selected LoRA is not compatible with the current Z-Image Nunchaku transformer. "
                    "Choose another Z-Image LoRA or fetch a compatible Nymphs Sprite LoRA profile."
                ) from exc
            continue

        raw_path = out_dir / f"{direction_name}_raw.png"
        source_metadata = source.with_suffix(".json")
        shutil.move(str(source), str(raw_path))
        if source_metadata.is_file():
            shutil.move(str(source_metadata), str(raw_path.with_suffix(".json")))
        try:
            source.parent.rmdir()
        except OSError:
            pass
        try:
            source.parent.parent.rmdir()
        except OSError:
            pass
        with Image.open(raw_path) as handle:
            raw_img = handle.convert("RGBA")
        pixel_path = out_dir / f"{direction_name}.png"
        if postprocess_output:
            cutout_img = normalize_to_square(
                remove_bg(raw_img, args.bg_tolerance, green_screen=not args.no_green_screen),
                args.crop_padding,
            )
            cutout_path = intermediate_dir / f"{direction_name}_cutout.png"
            cutout_img.save(cutout_path, "PNG")
            final_img = (
                pixelate(cutout_img, args.sprite_size, args.palette_colors)
                if pixelate_output
                else cutout_img
            )
            final_img.save(pixel_path, "PNG")
            cutout_paths[direction_name] = cutout_path
        else:
            raw_img.save(pixel_path, "PNG")

        raw_paths[direction_name] = raw_path
        pixel_paths[direction_name] = pixel_path
        direction_seeds[direction_name] = item_seed
        responses[direction_name] = response
        if control_image:
            controlnet_used.append(direction_name)
        generated_dirs.append(direction_name)
        print("OK")

    if not generated_dirs:
        raise SystemExit("No directions generated.")

    raw_sheet, pixel_sheet = make_contact_sheets(
        raw_paths,
        pixel_paths,
        directions=directions,
        display_name=display_name,
        stack="NymphScore_ZImage",
        sprite_size=args.sprite_size,
        final_label=(
            f"{args.sprite_size}x{args.sprite_size}"
            if pixelate_output
            else ("raw model output" if not postprocess_output else "normalized cutout")
        ),
        out_dir=out_dir,
        raw_cell_size=args.raw_cell_size,
        preview_cell_size=args.preview_cell_size,
    )
    print(f"\n  Raw inspection: {raw_sheet}")
    print(f"  Final contact:  {pixel_sheet}")

    recipe = {
        "stack": "NymphScore_ZImage",
        "model": args.model_id,
        "lora": lora_path,
        "debug_no_lora": bool(getattr(args, "debug_no_lora", False)),
        "lora_trigger": args.lora_trigger,
        "lora_scale": args.lora_scale,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "gen_size": f"{args.width}x{args.height}",
        "postprocess_enabled": postprocess_output,
        "pixelate": args.sprite_size if pixelate_output else False,
        "pixelate_enabled": pixelate_output,
        "seed": seed,
        "seed_step": args.seed_step,
        "direction_count": len(directions),
        "directions": [name for name, _ in directions],
        "subject_prompt": config["subject_prompt"],
        "negative": config.get("negative_prompt") or "",
        "nymphscore_url": args.nymphscore_url,
        "pose_lab_ref_set": str(pose_set_path) if pose_set_path else "",
        "controlnet_directions": controlnet_used,
        "controlnet_conditioning_scale": controlnet_scale if controlnet_used else None,
        "controlnet_guidance_scale": controlnet_guidance_scale if controlnet_used else None,
        "controlnet_mode": getattr(args, "controlnet_mode", "auto"),
        "controlnet_lora_mode": controlnet_lora_mode,
        "controlnet_lora_bypassed": controlnet_lora_bypassed,
        "lora_img2img_strength": args.lora_img2img_strength,
        "lora_stage2_directions": lora_stage2_used,
    }
    (out_dir / "recipe.json").write_text(json.dumps(recipe, indent=2), encoding="utf-8")
    (out_dir / "manifest.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "stack": "NymphScore_ZImage",
                "character": display_name,
                "seed": seed,
                "gen_size": f"{args.width}x{args.height}",
                "sprite_size": args.sprite_size,
                "postprocess_enabled": postprocess_output,
                "pixelate_enabled": pixelate_output,
                "timestamp": ts,
                "directions": generated_dirs,
                "direction_seeds": direction_seeds,
                "intermediate_cutouts": {name: str(cutout_paths[name]) for name in generated_dirs if name in cutout_paths},
                "pose_lab_ref_set": str(pose_set_path) if pose_set_path else "",
                "controlnet_directions": controlnet_used,
                "nymphs_image_responses": responses,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n  Generated {len(generated_dirs)}/{len(directions)} directions")
    print("\n--- Registering in foundry ---")
    foundry_cmd(
        "register-run",
        run_id,
        "--subject",
        subject_id,
        "--stack",
        "NymphScore_ZImage",
        "--seed",
        str(seed),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--target",
        str(args.sprite_size),
        "--recipe",
        str(out_dir / "recipe.json"),
    )

    for direction_name in generated_dirs:
        artifact_args = [
            "--artifacts",
            "raw",
            str(raw_paths[direction_name]),
            "--artifacts",
            "pixel",
            str(pixel_paths[direction_name]),
        ]
        if direction_name in cutout_paths:
            artifact_args.extend(["--artifacts", "cutout", str(cutout_paths[direction_name])])
        foundry_cmd(
            "register-attempt",
            run_id,
            direction_name,
            "--seed",
            str(direction_seeds[direction_name]),
            *artifact_args,
        )

    if not args.no_check:
        print("\n--- Running mechanical gates ---")
        foundry_cmd("check", run_id)

    print(f"\n{'=' * 60}")
    print(f"GENERATION COMPLETE: {display_name}")
    print(f"Run: {run_id}")
    print(f"Next: foundry review-show {run_id}")
    print(f"{'=' * 60}")
    return run_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Foundry sprites through NymphsCore/Nymphs Image.")
    parser.add_argument("--config", required=True, help="Path to character config JSON")
    parser.add_argument("--nymphscore-url", default=DEFAULT_NYMPHSCORE_URL)
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--lora-path", default="")
    parser.add_argument("--lora-trigger", default="pxlstl")
    parser.add_argument("--lora-scale", type=float, default=0.85)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--seed-step", type=int, default=1)
    parser.add_argument("--direction-count", type=int, default=8, choices=[8, 16])
    parser.add_argument("--guide-strength", default="normal", choices=["soft", "normal", "strong"])
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=9)
    parser.add_argument("--guidance-scale", type=float, default=0.0)
    parser.add_argument("--controlnet-guidance-scale", type=float, default=0.0)
    parser.add_argument("--controlnet-mode", default="auto", choices=["auto", "off"])
    parser.add_argument("--controlnet-lora-mode", default="on", choices=["on", "staged", "off"], help="on uses same-pass ControlNet + LoRA; staged runs ControlNet first, then LoRA img2img")
    parser.add_argument("--lora-img2img-strength", type=float, default=0.45, help="Strength for optional staged LoRA img2img refinement after Pose Lab ControlNet")
    parser.add_argument("--debug-no-lora", action="store_true", help="Diagnostic: run without LoRA to isolate ControlNet from LoRA merging")
    parser.add_argument("--max-directions", type=int, default=0, help="Diagnostic: generate only the first N directions")
    parser.add_argument("--nunchaku-rank", type=int, default=32)
    parser.add_argument("--nunchaku-precision", default="auto", choices=["auto", "int4", "fp4"])
    parser.add_argument("--sprite-size", type=int, default=96)
    parser.add_argument("--palette-colors", type=int, default=0)
    parser.add_argument("--no-postprocess", action="store_true", help="Save raw Z-Image outputs as final direction PNGs, skipping background removal, crop, normalize, and pixelation")
    parser.add_argument("--no-pixelate", action="store_true", help="Save normalized cutouts as final direction PNGs instead of pixelating to sprite size")
    parser.add_argument("--bg-tolerance", type=int, default=35)
    parser.add_argument("--crop-padding", type=float, default=0.08)
    parser.add_argument("--raw-cell-size", type=int, default=192)
    parser.add_argument("--preview-cell-size", type=int, default=192)
    parser.add_argument("--green-screen", dest="no_green_screen", action="store_false", default=False)
    parser.add_argument("--no-green-screen", dest="no_green_screen", action="store_true")
    parser.add_argument("--no-check", action="store_true", help="Skip immediate Foundry mechanical gates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    generate_and_register(config, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
