"""Nymphs Sprite integrated NymphsCore/Nymphs Image generation runner.

This preserves the inherited review, mechanical gates, maps, finish, and export
contracts while replacing the ComfyUI prompt queue with Nymphs Image's Z-Image
`/generate` API.

Usage:
    python -m pipeline.foundry_gen_nymphscore --config pipeline/chars/thal.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from foundry import db
from pipeline.nymphscore_client import generate_zimage, latest_lora_path, output_path


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
    draw.text((ox, oy), f"{display_name} -- {stack} ({sprite_size}x{sprite_size})", fill=(120, 200, 120), font=font(15))
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
) -> dict[str, Any]:
    negative = str(config.get("negative_prompt") or "")
    full_negative = f"{negative}, {NEGATIVE_BG}" if negative else NEGATIVE_BG
    prompt_parts = [
        args.lora_trigger,
        config["subject_prompt"],
        direction_prompt,
        STYLE_SUFFIX,
    ]
    return {
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
        "lora_path": lora_path,
        "lora_scale": args.lora_scale,
        "batch_id": batch_id,
        "batch_label": f"Nymphs Sprite: {config.get('display_name') or config['subject_id']}",
        "batch_type": "sprite_foundry_direction",
        "item_label": direction_name,
        "item_index": index,
        "item_total": direction_count,
        "output_dir": str(backend_dir),
    }


def selected_directions(args: argparse.Namespace) -> list[tuple[str, str]]:
    if int(args.direction_count) == 16:
        return DIRECTIONS_16
    return DIRECTIONS_8


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
    lora_path = args.lora_path or latest_lora_path(args.nymphscore_url)
    if not lora_path:
        raise SystemExit("No LoRA path supplied and Nymphs Image /api/loras returned no available LoRAs.")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"{subject_id}_nymphscore_{ts}"
    out_dir = Path.home() / "NymphsData" / "outputs" / "nymphs-sprite" / subject_id
    backend_root = Path.home() / "NymphsData" / "outputs" / "nymphs-sprite" / "_backend"
    clean_backend_staging(backend_root)
    backend_dir = backend_root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    backend_dir.mkdir(parents=True, exist_ok=True)
    all_direction_names = {name for name, _ in DIRECTIONS_8 + DIRECTIONS_16}
    for direction_name in all_direction_names:
        for suffix in (".png", "_raw.png", "_raw.json"):
            (out_dir / f"{direction_name}{suffix}").unlink(missing_ok=True)
    for filename in ("raw_inspection.png", "contact_sheet.png", "recipe.json", "manifest.json"):
        (out_dir / filename).unlink(missing_ok=True)

    print(f"\n{'=' * 60}")
    print(f"NYMPHSCORE GENERATION: {display_name}")
    print(f"Run: {run_id}  Seed: {seed}")
    print(f"Output: {out_dir}")
    print(f"Nymphs Image: {args.nymphscore_url}")
    print(f"Directions: {len(directions)}")
    print(f"{'=' * 60}\n")

    raw_paths: dict[str, Path] = {}
    pixel_paths: dict[str, Path] = {}
    generated_dirs: list[str] = []
    responses: dict[str, Any] = {}
    direction_seeds: dict[str, int] = {}

    for index, (direction_name, direction_prompt) in enumerate(directions, start=1):
        item_seed = seed + (index - 1) * args.seed_step
        print(f"  [{direction_name}] generate seed={item_seed}...", end=" ", flush=True)
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
        )
        try:
            response = generate_zimage(args.nymphscore_url, payload)
            source = output_path(response)
            if source is None or not source.exists():
                raise RuntimeError(f"missing output_path in response: {response}")
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
        pixel_img = pixelate(
            normalize_to_square(remove_bg(raw_img, args.bg_tolerance, green_screen=not args.no_green_screen), args.crop_padding),
            args.sprite_size,
            args.palette_colors,
        )
        pixel_path = out_dir / f"{direction_name}.png"
        pixel_img.save(pixel_path, "PNG")

        raw_paths[direction_name] = raw_path
        pixel_paths[direction_name] = pixel_path
        direction_seeds[direction_name] = item_seed
        responses[direction_name] = response
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
        out_dir=out_dir,
        raw_cell_size=args.raw_cell_size,
        preview_cell_size=args.preview_cell_size,
    )
    print(f"\n  Raw inspection: {raw_sheet}")
    print(f"  Pixel contact:  {pixel_sheet}")

    recipe = {
        "stack": "NymphScore_ZImage",
        "model": args.model_id,
        "lora": lora_path,
        "lora_trigger": args.lora_trigger,
        "lora_scale": args.lora_scale,
        "steps": args.steps,
        "guidance_scale": args.guidance_scale,
        "gen_size": f"{args.width}x{args.height}",
        "pixelate": args.sprite_size,
        "seed": seed,
        "seed_step": args.seed_step,
        "direction_count": len(directions),
        "directions": [name for name, _ in directions],
        "subject_prompt": config["subject_prompt"],
        "negative": config.get("negative_prompt") or "",
        "nymphscore_url": args.nymphscore_url,
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
                "timestamp": ts,
                "directions": generated_dirs,
                "direction_seeds": direction_seeds,
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
        foundry_cmd(
            "register-attempt",
            run_id,
            direction_name,
            "--seed",
            str(direction_seeds[direction_name]),
            "--artifacts",
            "raw",
            str(raw_paths[direction_name]),
            "--artifacts",
            "pixel",
            str(pixel_paths[direction_name]),
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
    parser.add_argument("--width", type=int, default=1024)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--steps", type=int, default=9)
    parser.add_argument("--guidance-scale", type=float, default=0.0)
    parser.add_argument("--nunchaku-rank", type=int, default=32)
    parser.add_argument("--nunchaku-precision", default="auto", choices=["auto", "int4", "fp4"])
    parser.add_argument("--sprite-size", type=int, default=96)
    parser.add_argument("--palette-colors", type=int, default=0)
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
