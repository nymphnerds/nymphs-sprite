"""
Pass A — Stack A Only: Pixel-Native (JuggernautXL + pixel-art-xl @ 0.85)

Generates Sera Vale in 8 directions, one at a time.
Saves raw + pixelated sprites, runs mechanical checks, builds contact sheet.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request

from PIL import Image, ImageDraw, ImageFont

COMFY_URL = "http://127.0.0.1:8188"
FOUNDRY_ROOT = Path(__file__).parent.parent
SPRITE_TARGET = 48
SEED = 424242

DIRECTIONS = [
    ("front", "facing the viewer, front view"),
    ("front_left", "facing front-left, 3/4 view from the left"),
    ("left", "facing left, side profile view"),
    ("back_left", "facing back-left, 3/4 rear view from the left"),
    ("back", "facing away from viewer, rear view"),
    ("back_right", "facing back-right, 3/4 rear view from the right"),
    ("right", "facing right, side profile view"),
    ("front_right", "facing front-right, 3/4 view from the right"),
]

SUBJECT_PROMPT = (
    "a single character sprite of a woman, Sera Vale, space merchant quartermaster, "
    "fitted utility vest over dark undershirt, wide belt at waist, "
    "rectangular satchel on left hip with cross-body strap, "
    "data-pad holster on right thigh, mid-calf boots, "
    "dark brown hair pulled back tight, no weapon, "
    "medium warm skin tone, muted tan vest, dark charcoal undershirt, "
    "dark brown belt and boots"
)

STYLE_SUFFIX = (
    "pixel art, game sprite, 2D RPG character, clean pixels, "
    "transparent background, centered on canvas, full body, standing idle pose, "
    "HD-2D style, crisp edges, deliberate pixel clusters"
)

NEGATIVE_PROMPT = (
    "blurry, smooth, photorealistic, 3D render, low quality, deformed, "
    "extra limbs, missing limbs, bad anatomy, bad hands, text, watermark, "
    "signature, frame, border, weapon, sword, gun, cape, hood, "
    "flowing hair, loose hair, busy background, multiple characters, "
    "cropped, cut off"
)


def make_workflow(direction_prompt: str, seed: int) -> dict:
    """Stack A: JuggernautXL + pixel-art-xl @ 0.85, euler_ancestral, 30 steps."""
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
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
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
                "cfg": 7.0,
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
                "filename_prefix": "stack_a",
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


def mechanical_check(img: Image.Image) -> dict:
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


def make_contact_sheet(images, run_id, output_path):
    CELL = 128
    PAD = 4
    LABEL_W = 80
    HEADER_H = 28
    CELL_W = CELL + PAD * 2
    CELL_H = CELL + PAD * 2
    BG = (24, 24, 32)
    TEXT = (200, 200, 210)
    ACCENT = (120, 160, 200)
    GRID = (50, 50, 60)

    total_w = LABEL_W + 8 * CELL_W + 20
    total_h = 10 + 24 + HEADER_H + CELL_H + 10 + 130 + 20
    img = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_sm = ImageFont.truetype("consola.ttf", 11)
        font_md = ImageFont.truetype("consola.ttf", 13)
        font_lg = ImageFont.truetype("consola.ttf", 15)
    except (OSError, IOError):
        font_sm = font_md = font_lg = ImageFont.load_default()

    ox, oy = 10, 10
    draw.text((ox, oy), "PASS A — Stack A: Pixel-Native", fill=ACCENT, font=font_lg)
    oy += 24

    dir_names = [d[0] for d in DIRECTIONS]
    for col, name in enumerate(dir_names):
        draw.text((ox + LABEL_W + col * CELL_W + PAD, oy + 2), name.replace("_", "\n"), fill=TEXT, font=font_sm)
    oy += HEADER_H

    draw.text((ox + 4, oy + CELL // 2), "Albedo", fill=ACCENT, font=font_md)
    for col, name in enumerate(dir_names):
        cx = ox + LABEL_W + col * CELL_W + PAD
        cy = oy + PAD
        if name in images:
            sprite = images[name].copy()
            display = sprite.resize((CELL, CELL), Image.NEAREST)
            cell_bg = Image.new("RGBA", (CELL, CELL), (40, 40, 50, 255))
            cell_bg.paste(display, (0, 0), display if display.mode == "RGBA" else None)
            img.paste(cell_bg.convert("RGB"), (cx, cy))
        else:
            draw.rectangle([cx, cy, cx + CELL, cy + CELL], fill=(60, 30, 30), outline=GRID)
            draw.text((cx + 10, cy + CELL // 2 - 6), "MISSING", fill=(200, 80, 80), font=font_sm)

    oy += CELL_H + 10
    draw.line([(ox, oy), (total_w - 10, oy)], fill=GRID)
    oy += 6
    draw.text((ox, oy), "RUN METADATA", fill=ACCENT, font=font_md)
    oy += 18
    for line in [
        f"Run ID:     {run_id}",
        f"Stack:      A — Pixel-Native (JuggernautXL + pixel-art-xl @ 0.85)",
        f"Character:  Sera Vale",
        f"Seed:       {SEED}",
        f"Target:     {SPRITE_TARGET}x{SPRITE_TARGET}",
        f"Generated:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Directions: {len(images)}/8",
    ]:
        draw.text((ox + 8, oy), line, fill=TEXT, font=font_sm)
        oy += 14

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def run():
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"stack_a_{ts}"
    out_dir = FOUNDRY_ROOT / "bakeoff" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    images = {}
    manifest_items = []
    mech_results = {}

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

            raw_path = out_dir / f"{dir_name}_raw.png"
            with open(raw_path, "wb") as f:
                f.write(img_data)

            raw_img = Image.open(raw_path).convert("RGBA")
            pixel_img = raw_img.resize((SPRITE_TARGET, SPRITE_TARGET), Image.NEAREST)
            pixel_path = out_dir / f"{dir_name}.png"
            pixel_img.save(str(pixel_path), "PNG")

            images[dir_name] = pixel_img
            mech = mechanical_check(pixel_img)
            mech_results[dir_name] = mech

            status = "PASS" if mech["pass"] else f"FAIL({','.join(mech['issues'])})"
            print(f"OK  mech:{status}")

            manifest_items.append({
                "direction": dir_name,
                "raw": str(raw_path),
                "pixel": str(pixel_path),
                "seed": SEED,
                "mechanical": mech,
            })
        except Exception as e:
            print(f"EXTRACT FAIL: {e}")
            continue

    # Contact sheet
    sheet = out_dir / "contact_sheet_A.png"
    make_contact_sheet(images, run_id, sheet)
    print(f"\n  Contact sheet: {sheet}")

    # Manifest
    manifest = {
        "run_id": run_id,
        "stack": "A",
        "stack_name": "Pixel-Native",
        "seed": SEED,
        "timestamp": ts,
        "directions": len(images),
        "mechanical_passes": sum(1 for m in mech_results.values() if m["pass"]),
        "items": manifest_items,
    }
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Recipe
    with open(out_dir / "recipe.json", "w") as f:
        json.dump({
            "stack": "A",
            "checkpoint": "juggernautXL_ragnarokBy.safetensors",
            "lora": "pixel-art-xl.safetensors @ 0.85",
            "sampler": "euler_ancestral",
            "steps": 30,
            "cfg": 7.0,
            "gen_size": "512x512",
            "pixelate": SPRITE_TARGET,
            "seed": SEED,
            "subject_prompt": SUBJECT_PROMPT,
            "style_suffix": STYLE_SUFFIX,
            "negative": NEGATIVE_PROMPT,
        }, f, indent=2)

    print(f"\n  Stack A complete: {len(images)}/8 directions")
    print(f"  Mechanical passes: {sum(1 for m in mech_results.values() if m['pass'])}/8")
    print(f"  Output: {out_dir}")
    return out_dir


if __name__ == "__main__":
    run()
