"""
Pass A.6 — Single-Subject Re-stabilization

Stack A v2: same winning stack, stronger single-subject isolation.

Changes from v1:
- "solo" + "1woman" + "single character" emphasis in prompt
- Stronger multi-figure negative prompts
- 768x768 generation (more canvas = less pressure to fill with second figure)
- Taller aspect option: 576x768 to encourage single full-body portrait
- Raw 512/768 inspection BEFORE downscale
- New mechanical gate: raw-source single-subject check

Generates Sera Vale in 8 directions, one at a time.
Saves raw + builds raw-resolution contact sheet for source inspection.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

from PIL import Image, ImageDraw, ImageFont
import numpy as np

COMFY_URL = "http://127.0.0.1:8188"
FOUNDRY_ROOT = Path(__file__).parent.parent
SPRITE_TARGET = 48
SEED = 505050  # fresh seed for v2

DIRECTIONS = [
    ("front", "facing the viewer, front view, looking at camera"),
    ("front_left", "facing front-left, 3/4 view from the left, looking slightly left"),
    ("left", "facing left, left side profile view"),
    ("back_left", "facing back-left, 3/4 rear view from the left"),
    ("back", "facing away from viewer, rear view, back of character"),
    ("back_right", "facing back-right, 3/4 rear view from the right"),
    ("right", "facing right, right side profile view"),
    ("front_right", "facing front-right, 3/4 view from the right, looking slightly right"),
]

# Stronger single-subject prompt
SUBJECT_PROMPT = (
    "solo, 1woman, single character only, one person, "
    "a woman named Sera Vale, space merchant quartermaster, "
    "fitted utility vest over dark undershirt, wide belt at waist, "
    "rectangular satchel on left hip with cross-body strap, "
    "data-pad holster on right thigh, mid-calf boots, "
    "dark brown hair pulled back tight in a bun, no weapon, "
    "medium warm skin tone, muted tan vest, dark charcoal undershirt, "
    "dark brown belt and boots, standing idle neutral pose"
)

STYLE_SUFFIX = (
    "pixel art sprite, game character sprite, 2D RPG, clean pixel art, "
    "solid color background, centered composition, full body shot, "
    "character centered in frame, HD-2D inspired, crisp pixel edges, "
    "single character portrait, character design, isolated figure"
)

# Much stronger anti-multi-subject negatives
NEGATIVE_PROMPT = (
    "multiple people, two characters, group, couple, pair, reflection, mirror, "
    "side by side, comparison, turnaround sheet, model sheet, reference sheet, "
    "split view, dual view, before and after, "
    "blurry, smooth, photorealistic, 3D render, low quality, deformed, "
    "extra limbs, missing limbs, bad anatomy, bad hands, text, watermark, "
    "signature, frame, border, weapon, sword, gun, cape, hood, "
    "flowing hair, loose hair, busy background, "
    "cropped, cut off, partial body"
)

# Use portrait aspect to discourage side-by-side composition
GEN_WIDTH = 576
GEN_HEIGHT = 768


def make_workflow(direction_prompt: str, seed: int) -> dict:
    """Stack A v2: JuggernautXL + pixel-art-xl @ 0.85, portrait aspect, isolation emphasis."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "juggernautXL_ragnarokBy.safetensors"},
        },
        "2": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["1", 0],
                "clip": ["1", 1],
                "lora_name": "pixel-art-xl.safetensors",
                "strength_model": 0.85,
                "strength_clip": 0.85,
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 1],
                "text": f"{SUBJECT_PROMPT}, {direction_prompt}, {STYLE_SUFFIX}",
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 1],
                "text": NEGATIVE_PROMPT,
            },
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": GEN_WIDTH, "height": GEN_HEIGHT, "batch_size": 1},
        },
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["2", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["5", 0],
                "seed": seed,
                "steps": 30,
                "cfg": 7.5,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
        "7": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["1", 2],
            },
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": "stack_a_v2",
            },
        },
    }


def queue_prompt(workflow):
    data = json.dumps({"prompt": workflow}).encode()
    req = Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        return json.loads(resp.read())


def wait_for_completion(prompt_id, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(3)
    raise TimeoutError(f"Prompt {prompt_id} timed out after {timeout}s")


def get_image(filename, subfolder=""):
    params = f"filename={filename}&subfolder={subfolder}&type=output"
    with urlopen(f"{COMFY_URL}/view?{params}") as resp:
        return resp.read()


def raw_source_check(img: Image.Image) -> dict:
    """Check raw source for multi-subject composition.

    Strategy: split image into left and right halves, check if both halves
    contain significant opaque content (suggesting two figures).
    Also check center-of-mass to detect off-center composition.
    """
    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]

    # Find non-background pixels (rough: anything not close to the dominant corner color)
    corners = np.array([arr[0, 0, :3], arr[0, w-1, :3], arr[h-1, 0, :3], arr[h-1, w-1, :3]], dtype=np.float32)
    bg = np.mean(corners, axis=0)
    diff = np.sqrt(np.sum((arr[:, :, :3].astype(np.float32) - bg) ** 2, axis=2))
    fg_mask = diff > 40  # foreground pixels

    total_fg = np.sum(fg_mask)
    if total_fg == 0:
        return {"pass": False, "issues": ["empty_frame"]}

    issues = []

    # Split into left/right thirds
    third = w // 3
    left_fg = np.sum(fg_mask[:, :third])
    center_fg = np.sum(fg_mask[:, third:2*third])
    right_fg = np.sum(fg_mask[:, 2*third:])

    # If both left and right thirds have significant content, likely multi-subject
    left_ratio = left_fg / max(total_fg, 1)
    right_ratio = right_fg / max(total_fg, 1)
    center_ratio = center_fg / max(total_fg, 1)

    if left_ratio > 0.25 and right_ratio > 0.25 and center_ratio < 0.35:
        issues.append("multi_subject_composition")

    # Check if figure is reasonably centered
    fg_coords = np.where(fg_mask)
    if len(fg_coords[1]) > 0:
        com_x = np.mean(fg_coords[1]) / w
        if com_x < 0.3 or com_x > 0.7:
            issues.append(f"off_center:{com_x:.2f}")

    return {"pass": len(issues) == 0, "issues": issues}


def mechanical_check_48(img: Image.Image) -> dict:
    """Standard 48x48 mechanical checks."""
    issues = []
    if img.size != (SPRITE_TARGET, SPRITE_TARGET):
        issues.append(f"wrong_size:{img.size}")
    if img.mode != "RGBA":
        issues.append(f"no_alpha:{img.mode}")
    else:
        corners = [img.getpixel((0, 0)), img.getpixel((47, 0)),
                    img.getpixel((0, 47)), img.getpixel((47, 47))]
        opaque = sum(1 for c in corners if c[3] > 128)
        if opaque >= 3:
            issues.append("background_opaque")
    return {"pass": len(issues) == 0, "issues": issues}


def remove_bg(img, tolerance=35):
    """Remove near-uniform background."""
    arr = np.array(img.convert("RGBA")).copy()
    h, w = arr.shape[:2]
    corners = [arr[0, 0, :3], arr[0, w-1, :3], arr[h-1, 0, :3], arr[h-1, w-1, :3]]
    bg_color = np.mean(corners, axis=0).astype(np.float32)
    rgb = arr[:, :, :3].astype(np.float32)
    diff = np.sqrt(np.sum((rgb - bg_color) ** 2, axis=2))
    arr[diff < tolerance, 3] = 0
    return Image.fromarray(arr)


def make_raw_contact_sheet(raw_images, run_id, output_path):
    """Contact sheet at RAW resolution for source inspection."""
    CELL = 192  # show raw at reduced but readable size
    PAD = 4
    LABEL_W = 90
    HEADER_H = 28
    CELL_W = CELL + PAD * 2
    CELL_H = int(CELL * GEN_HEIGHT / GEN_WIDTH) + PAD * 2
    BG = (24, 24, 32)
    TEXT = (200, 200, 210)
    ACCENT = (200, 120, 120)  # red accent for raw inspection
    GRID = (50, 50, 60)

    total_w = LABEL_W + 8 * CELL_W + 20
    total_h = 10 + 24 + HEADER_H + CELL_H + 10 + 60 + 20
    img = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_sm = ImageFont.truetype("consola.ttf", 11)
        font_md = ImageFont.truetype("consola.ttf", 13)
        font_lg = ImageFont.truetype("consola.ttf", 15)
    except (OSError, IOError):
        font_sm = font_md = font_lg = ImageFont.load_default()

    ox, oy = 10, 10
    draw.text((ox, oy), f"RAW SOURCE INSPECTION — Stack A v2", fill=ACCENT, font=font_lg)
    oy += 24

    dir_names = [d[0] for d in DIRECTIONS]
    for col, name in enumerate(dir_names):
        draw.text((ox + LABEL_W + col * CELL_W + PAD, oy + 2), name.replace("_", "\n"), fill=TEXT, font=font_sm)
    oy += HEADER_H

    draw.text((ox + 2, oy + CELL_H // 2 - 6), "Raw\n576x768", fill=ACCENT, font=font_sm)
    cell_h_inner = int(CELL * GEN_HEIGHT / GEN_WIDTH)
    for col, name in enumerate(dir_names):
        cx = ox + LABEL_W + col * CELL_W + PAD
        cy = oy + PAD
        if name in raw_images:
            raw = raw_images[name].resize((CELL, cell_h_inner), Image.LANCZOS)
            img.paste(raw, (cx, cy))
        else:
            draw.rectangle([cx, cy, cx + CELL, cy + cell_h_inner], fill=(60, 30, 30), outline=GRID)

    oy += CELL_H + 10
    draw.line([(ox, oy), (total_w - 10, oy)], fill=GRID)
    oy += 6
    draw.text((ox, oy), f"Run: {run_id} | Check for: single subject, centered, no reflection/companion", fill=TEXT, font=font_sm)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def make_pixel_contact_sheet(pixel_images, run_id, output_path):
    """48x48 contact sheet with checkerboard background."""
    CELL = 128
    PAD = 4
    LABEL_W = 80
    HEADER_H = 28
    CELL_W = CELL + PAD * 2
    CELL_H = CELL + PAD * 2
    BG = (24, 24, 32)
    TEXT = (200, 200, 210)
    ACCENT = (120, 200, 120)
    GRID = (50, 50, 60)

    total_w = LABEL_W + 8 * CELL_W + 20
    total_h = 10 + 24 + HEADER_H + CELL_H + 10 + 60 + 20
    img = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_sm = ImageFont.truetype("consola.ttf", 11)
        font_md = ImageFont.truetype("consola.ttf", 13)
        font_lg = ImageFont.truetype("consola.ttf", 15)
    except (OSError, IOError):
        font_sm = font_md = font_lg = ImageFont.load_default()

    ox, oy = 10, 10
    draw.text((ox, oy), "PASS A.6 — Stack A v2 (single-subject isolation)", fill=ACCENT, font=font_lg)
    oy += 24

    dir_names = [d[0] for d in DIRECTIONS]
    for col, name in enumerate(dir_names):
        draw.text((ox + LABEL_W + col * CELL_W + PAD, oy + 2), name.replace("_", "\n"), fill=TEXT, font=font_sm)
    oy += HEADER_H

    draw.text((ox + 4, oy + CELL // 2), "Albedo", fill=ACCENT, font=font_md)
    for col, name in enumerate(dir_names):
        cx = ox + LABEL_W + col * CELL_W + PAD
        cy = oy + PAD
        if name in pixel_images:
            sprite = pixel_images[name].copy()
            display = sprite.resize((CELL, CELL), Image.NEAREST)
            checker = Image.new("RGB", (CELL, CELL))
            cd = ImageDraw.Draw(checker)
            for y2 in range(0, CELL, 8):
                for x2 in range(0, CELL, 8):
                    c = (45, 45, 55) if (x2 // 8 + y2 // 8) % 2 == 0 else (35, 35, 45)
                    cd.rectangle([x2, y2, x2 + 7, y2 + 7], fill=c)
            checker.paste(display, (0, 0), display if display.mode == "RGBA" else None)
            img.paste(checker, (cx, cy))
        else:
            draw.rectangle([cx, cy, cx + CELL, cy + CELL], fill=(60, 30, 30), outline=GRID)

    oy += CELL_H + 10
    draw.line([(ox, oy), (total_w - 10, oy)], fill=GRID)
    oy += 6
    draw.text((ox, oy), f"Run: {run_id} | bg removed, portrait aspect 576x768", fill=TEXT, font=font_sm)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def run():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"stack_a_v2_{ts}"
    out_dir = FOUNDRY_ROOT / "bakeoff" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    raw_images = {}
    pixel_images = {}
    manifest_items = []

    for dir_name, dir_prompt in DIRECTIONS:
        print(f"  [{dir_name}] submitting...", end=" ", flush=True)

        workflow = make_workflow(dir_prompt, SEED)
        try:
            resp = queue_prompt(workflow)
            pid = resp["prompt_id"]
        except Exception as e:
            print(f"SUBMIT FAIL: {e}")
            continue

        print(f"queued ({pid[:8]}), waiting...", end=" ", flush=True)

        try:
            history = wait_for_completion(pid)
        except TimeoutError:
            print("TIMEOUT")
            continue

        try:
            img_info = history["outputs"]["8"]["images"][0]
            img_data = get_image(img_info["filename"], img_info.get("subfolder", ""))

            # Save raw
            raw_path = out_dir / f"{dir_name}_raw.png"
            with open(raw_path, "wb") as f:
                f.write(img_data)
            raw_img = Image.open(raw_path)
            raw_images[dir_name] = raw_img

            # Raw source check (multi-subject detection)
            src_check = raw_source_check(raw_img)
            src_status = "PASS" if src_check["pass"] else f"FAIL({','.join(src_check['issues'])})"

            # Background removal + pixelate
            cleaned = remove_bg(raw_img.convert("RGBA"))

            # Center-crop to square before downscale (portrait → square)
            w, h = cleaned.size
            if h > w:
                top = (h - w) // 4  # crop slightly above center for full body
                cleaned = cleaned.crop((0, top, w, top + w))

            pixel_img = cleaned.resize((SPRITE_TARGET, SPRITE_TARGET), Image.NEAREST)
            pixel_path = out_dir / f"{dir_name}.png"
            pixel_img.save(str(pixel_path))
            pixel_images[dir_name] = pixel_img

            # 48x48 mechanical check
            mech = mechanical_check_48(pixel_img)
            mech_status = "PASS" if mech["pass"] else f"FAIL({','.join(mech['issues'])})"

            print(f"OK  src:{src_status}  mech:{mech_status}")

            manifest_items.append({
                "direction": dir_name,
                "raw": str(raw_path),
                "pixel": str(pixel_path),
                "seed": SEED,
                "source_check": src_check,
                "mechanical": mech,
            })
        except Exception as e:
            print(f"EXTRACT FAIL: {e}")
            continue

    # Build both contact sheets
    raw_sheet = out_dir / "raw_inspection.png"
    make_raw_contact_sheet(raw_images, run_id, raw_sheet)
    print(f"\n  Raw inspection sheet: {raw_sheet}")

    pixel_sheet = out_dir / "contact_sheet_A_v2.png"
    make_pixel_contact_sheet(pixel_images, run_id, pixel_sheet)
    print(f"  Pixel contact sheet: {pixel_sheet}")

    # Manifest
    src_passes = sum(1 for item in manifest_items if item["source_check"]["pass"])
    manifest = {
        "run_id": run_id,
        "stack": "A_v2",
        "stack_name": "Pixel-Native v2 (single-subject isolation)",
        "seed": SEED,
        "gen_size": f"{GEN_WIDTH}x{GEN_HEIGHT}",
        "timestamp": ts,
        "directions": len(pixel_images),
        "source_check_passes": src_passes,
        "items": manifest_items,
    }
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n  Stack A v2 complete: {len(pixel_images)}/8 directions")
    print(f"  Source check passes: {src_passes}/8")
    print(f"  Output: {out_dir}")
    return out_dir


if __name__ == "__main__":
    run()
