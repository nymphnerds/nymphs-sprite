"""
Pass A Bakeoff Runner — generates 8-direction albedo sets for each stack archetype.

Submits workflows to ComfyUI headless API, collects outputs, runs mechanical checks,
and generates contact-sheet review artifacts.

Usage:
    python pipeline/bakeoff_runner.py
"""

import json
import os
import random
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

from PIL import Image

COMFY_URL = "http://127.0.0.1:8188"
FOUNDRY_ROOT = Path(__file__).parent.parent
OUTPUT_ROOT = FOUNDRY_ROOT / "bakeoff"
SPRITE_TARGET = 48

# --- Subject lock (from subject-sheet.md) ---
SUBJECT = {
    "name": "Sera Vale",
    "character_id": "sera_vale",
    "role": "Crew Broker / Quartermaster",
    "sprite_size": SPRITE_TARGET,
}

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

# --- Shared prompt components (identical for all stacks) ---
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

# --- Stack definitions ---

def make_stack_a_workflow(direction_prompt: str, seed: int) -> dict:
    """Stack A — Pixel-Native: JuggernautXL + pixel-art-xl LoRA at high weight."""
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
                "filename_prefix": "bakeoff_a",
            },
        },
    }


def make_stack_b_workflow(direction_prompt: str, seed: int) -> dict:
    """Stack B — Stylized + Cleanup: JuggernautXL + PixelArtRedmond LoRA, moderate weight."""
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
                "lora_name": "PixelArtRedmond-Lite64.safetensors",
                "strength_model": 0.7,
                "strength_clip": 0.7,
            },
        },
        "2b": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["2", 0],
                "clip": ["2", 1],
                "lora_name": "DetailTweakerXL.safetensors",
                "strength_model": 0.4,
                "strength_clip": 0.4,
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2b", 1],
                "text": f"PixArFK, {SUBJECT_PROMPT}, {direction_prompt}, {STYLE_SUFFIX}",
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2b", 1],
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
                "model": ["2b", 0],
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
                "filename_prefix": "bakeoff_b",
            },
        },
    }


def make_stack_c_workflow(direction_prompt: str, seed: int) -> dict:
    """Stack C — Reference Control: JuggernautXL + pixel-art-xl + ControlNet depth conditioning.

    For Pass A (no reference image yet), Stack C runs with stronger prompt engineering
    and higher cfg to compensate for missing IP-Adapter reference. The reference-heavy
    aspect will be tested in a second pass if Pass A identity holds.
    """
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
                "strength_model": 0.75,
                "strength_clip": 0.75,
            },
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 1],
                "text": (
                    f"character turnaround sheet, {SUBJECT_PROMPT}, {direction_prompt}, "
                    f"{STYLE_SUFFIX}, consistent character design, reference sheet style"
                ),
            },
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 1],
                "text": NEGATIVE_PROMPT + ", inconsistent design, different characters",
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
                "steps": 35,
                "cfg": 8.5,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
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
                "filename_prefix": "bakeoff_c",
            },
        },
    }


STACKS = {
    "A": {
        "name": "Pixel-Native",
        "description": "JuggernautXL + pixel-art-xl @ 0.85",
        "make_workflow": make_stack_a_workflow,
    },
    "B": {
        "name": "Stylized + Cleanup",
        "description": "JuggernautXL + PixelArtRedmond @ 0.7 + DetailTweaker @ 0.4",
        "make_workflow": make_stack_b_workflow,
    },
    "C": {
        "name": "Reference Control",
        "description": "JuggernautXL + pixel-art-xl @ 0.75, higher cfg, turnaround prompting",
        "make_workflow": make_stack_c_workflow,
    },
}


# --- ComfyUI API helpers ---

def queue_prompt(workflow: dict, client_id: str | None = None) -> dict:
    """Submit a workflow to ComfyUI and return the prompt response."""
    payload = {"prompt": workflow}
    if client_id:
        payload["client_id"] = client_id

    data = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(req) as resp:
        return json.loads(resp.read())


def get_history(prompt_id: str) -> dict:
    """Get execution history for a prompt."""
    with urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
        return json.loads(resp.read())


def wait_for_completion(prompt_id: str, timeout: int = 300) -> dict:
    """Poll until a prompt completes or times out."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            history = get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} did not complete within {timeout}s")


def get_image(filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
    """Download an output image from ComfyUI."""
    params = f"filename={filename}&subfolder={subfolder}&type={folder_type}"
    with urlopen(f"{COMFY_URL}/view?{params}") as resp:
        return resp.read()


# --- Contact sheet generation ---

def make_contact_sheet(
    images: dict[str, Image.Image],
    stack_id: str,
    stack_name: str,
    run_id: str,
    seed: int,
    output_path: Path,
) -> Path:
    """Generate a contact-sheet PNG from 8 direction albedo images."""
    from PIL import ImageDraw, ImageFont

    CELL = 128  # display size per sprite on contact sheet
    PAD = 4
    COLS = 8
    LABEL_W = 80
    HEADER_H = 28
    CELL_W = CELL + PAD * 2
    CELL_H = CELL + PAD * 2

    BG = (24, 24, 32)
    TEXT = (200, 200, 210)
    ACCENT = (120, 160, 200)
    GRID = (50, 50, 60)

    dir_names = [d[0] for d in DIRECTIONS]
    total_w = LABEL_W + COLS * CELL_W + 20
    meta_h = 120
    total_h = 10 + 24 + HEADER_H + CELL_H + 10 + meta_h + 20

    img = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_sm = ImageFont.truetype("consola.ttf", 11)
        font_md = ImageFont.truetype("consola.ttf", 13)
        font_lg = ImageFont.truetype("consola.ttf", 15)
    except (OSError, IOError):
        font_sm = font_md = font_lg = ImageFont.load_default()

    ox, oy = 10, 10
    draw.text((ox, oy), f"PASS A — Stack {stack_id}: {stack_name}", fill=ACCENT, font=font_lg)
    oy += 24

    # Column headers
    for col, (dir_name, _) in enumerate(DIRECTIONS):
        cx = ox + LABEL_W + col * CELL_W + PAD
        label = dir_name.replace("_", "\n")
        draw.text((cx, oy + 2), label, fill=TEXT, font=font_sm)
    oy += HEADER_H

    # Albedo row
    draw.text((ox + 4, oy + CELL // 2), "Albedo", fill=ACCENT, font=font_md)
    for col, (dir_name, _) in enumerate(DIRECTIONS):
        cx = ox + LABEL_W + col * CELL_W + PAD
        cy = oy + PAD

        if dir_name in images:
            sprite = images[dir_name].copy()
            # Scale up for visibility (nearest neighbor to keep pixels)
            display = sprite.resize((CELL, CELL), Image.NEAREST)
            # Paste onto a dark background for visibility
            cell_bg = Image.new("RGBA", (CELL, CELL), (40, 40, 50, 255))
            cell_bg.paste(display, (0, 0), display if display.mode == "RGBA" else None)
            img.paste(cell_bg.convert("RGB"), (cx, cy))
        else:
            draw.rectangle([cx, cy, cx + CELL, cy + CELL], fill=(60, 30, 30), outline=GRID)
            draw.text((cx + 10, cy + CELL // 2 - 6), "MISSING", fill=(200, 80, 80), font=font_sm)

    oy += CELL_H + 10

    # Metadata
    draw.line([(ox, oy), (total_w - 10, oy)], fill=GRID)
    oy += 6
    draw.text((ox, oy), "RUN METADATA", fill=ACCENT, font=font_md)
    oy += 18
    meta_lines = [
        f"Run ID:     {run_id}",
        f"Stack:      {stack_id} — {stack_name}",
        f"Character:  {SUBJECT['name']}",
        f"Seed:       {seed}",
        f"Target:     {SPRITE_TARGET}x{SPRITE_TARGET}",
        f"Generated:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Directions: {len(images)}/8 present",
    ]
    for line in meta_lines:
        draw.text((ox + 8, oy), line, fill=TEXT, font=font_sm)
        oy += 14

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


# --- Pixelation ---

def pixelate(src: Image.Image, target: int = 48) -> Image.Image:
    """Nearest-neighbor downscale to target size."""
    return src.resize((target, target), Image.NEAREST)


# --- Mechanical checks ---

def mechanical_check(sprite_path: Path, direction: str) -> dict:
    """Run Pass A mechanical validation on a single sprite."""
    issues = []
    try:
        img = Image.open(sprite_path)
    except Exception as e:
        return {"pass": False, "issues": [f"cannot_open: {e}"]}

    # Canvas size
    if img.size != (SPRITE_TARGET, SPRITE_TARGET):
        issues.append(f"wrong_size: {img.size} expected {SPRITE_TARGET}x{SPRITE_TARGET}")

    # Transparency
    if img.mode != "RGBA":
        issues.append(f"no_alpha: mode={img.mode}")
    else:
        # Check corners for transparency (should be transparent background)
        corners = [img.getpixel((0, 0)), img.getpixel((47, 0)), img.getpixel((0, 47)), img.getpixel((47, 47))]
        opaque_corners = sum(1 for c in corners if c[3] > 128)
        if opaque_corners >= 3:
            issues.append("background_not_transparent: >=3 opaque corners")

    # Check not cropped (character should not touch edges heavily)
    # This is a soft check — just flag if >30% of edge pixels are opaque
    if img.mode == "RGBA":
        edge_pixels = []
        for x in range(SPRITE_TARGET):
            edge_pixels.append(img.getpixel((x, 0))[3])
            edge_pixels.append(img.getpixel((x, SPRITE_TARGET - 1))[3])
        for y in range(SPRITE_TARGET):
            edge_pixels.append(img.getpixel((0, y))[3])
            edge_pixels.append(img.getpixel((SPRITE_TARGET - 1, y))[3])
        opaque_edge_ratio = sum(1 for p in edge_pixels if p > 128) / len(edge_pixels)
        if opaque_edge_ratio > 0.30:
            issues.append(f"possible_crop: {opaque_edge_ratio:.0%} edge pixels opaque")

    return {"pass": len(issues) == 0, "issues": issues}


# --- Main bakeoff runner ---

def run_bakeoff():
    """Execute Pass A bakeoff for all three stacks."""
    # Use a fixed seed per stack for reproducibility, different between stacks
    base_seed = 424242
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    results = {}

    for stack_id, stack_info in STACKS.items():
        stack_seed = base_seed + (ord(stack_id) * 1000)
        run_id = f"bakeoff_{stack_id}_{run_timestamp}"
        stack_dir = OUTPUT_ROOT / run_id
        stack_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Stack {stack_id}: {stack_info['name']}")
        print(f"Run ID: {run_id}")
        print(f"Seed: {stack_seed}")
        print(f"{'='*60}")

        images = {}
        manifests = []
        mechanical_results = {}

        for dir_name, dir_prompt in DIRECTIONS:
            print(f"  Generating {dir_name}...", end=" ", flush=True)

            # Build and submit workflow
            workflow = stack_info["make_workflow"](dir_prompt, stack_seed)
            try:
                result = queue_prompt(workflow)
                prompt_id = result["prompt_id"]
            except Exception as e:
                print(f"SUBMIT FAILED: {e}")
                continue

            # Wait for completion
            try:
                history = wait_for_completion(prompt_id, timeout=120)
            except TimeoutError:
                print("TIMEOUT")
                continue

            # Extract output image
            try:
                outputs = history.get("outputs", {})
                save_node = outputs.get("8", {})
                image_list = save_node.get("images", [])
                if not image_list:
                    print("NO OUTPUT")
                    continue

                img_info = image_list[0]
                img_data = get_image(img_info["filename"], img_info.get("subfolder", ""))

                # Save raw output
                raw_path = stack_dir / f"{dir_name}_raw.png"
                with open(raw_path, "wb") as f:
                    f.write(img_data)

                # Pixelate to 48x48
                raw_img = Image.open(raw_path).convert("RGBA")
                pixel_img = pixelate(raw_img, SPRITE_TARGET)
                pixel_path = stack_dir / f"{dir_name}.png"
                pixel_img.save(str(pixel_path), "PNG")

                images[dir_name] = pixel_img

                # Mechanical check
                mech = mechanical_check(pixel_path, dir_name)
                mechanical_results[dir_name] = mech
                status = "PASS" if mech["pass"] else f"FAIL: {', '.join(mech['issues'])}"
                print(f"OK → mech: {status}")

                manifests.append({
                    "direction": dir_name,
                    "raw_path": str(raw_path),
                    "pixel_path": str(pixel_path),
                    "seed": stack_seed,
                    "mechanical": mech,
                })

            except Exception as e:
                print(f"EXTRACT FAILED: {e}")
                continue

        # Generate contact sheet
        sheet_path = stack_dir / f"contact_sheet_{stack_id}.png"
        make_contact_sheet(images, stack_id, stack_info["name"], run_id, stack_seed, sheet_path)
        print(f"\n  Contact sheet: {sheet_path}")

        # Save manifest
        manifest = {
            "run_id": run_id,
            "stack_id": stack_id,
            "stack_name": stack_info["name"],
            "stack_description": stack_info["description"],
            "character": SUBJECT,
            "seed": stack_seed,
            "timestamp": run_timestamp,
            "directions_generated": len(images),
            "directions_total": 8,
            "mechanical_pass_count": sum(1 for m in mechanical_results.values() if m["pass"]),
            "items": manifests,
        }
        manifest_path = stack_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Save generation recipe
        recipe = {
            "stack_id": stack_id,
            "checkpoint": "juggernautXL_ragnarokBy.safetensors",
            "loras": stack_info["description"],
            "subject_prompt": SUBJECT_PROMPT,
            "style_suffix": STYLE_SUFFIX,
            "negative_prompt": NEGATIVE_PROMPT,
            "seed": stack_seed,
            "generation_size": "512x512",
            "pixelate_target": SPRITE_TARGET,
        }
        recipe_path = stack_dir / "recipe.json"
        with open(recipe_path, "w") as f:
            json.dump(recipe, f, indent=2)

        results[stack_id] = {
            "run_id": run_id,
            "images_generated": len(images),
            "mechanical_passes": sum(1 for m in mechanical_results.values() if m["pass"]),
            "contact_sheet": str(sheet_path),
            "manifest": str(manifest_path),
        }

    # Summary
    print(f"\n{'='*60}")
    print("BAKEOFF SUMMARY")
    print(f"{'='*60}")
    for sid, r in results.items():
        print(f"  Stack {sid}: {r['images_generated']}/8 generated, {r['mechanical_passes']}/8 mechanical pass")
        print(f"    Contact sheet: {r['contact_sheet']}")
    print(f"\nReview artifacts in: {OUTPUT_ROOT}")

    return results


if __name__ == "__main__":
    run_bakeoff()
