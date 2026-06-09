"""
Phase 1C.2 — Kael Morrow Map Derivation (Probe: 4 directions)

Derives normal + depth maps from raw albedo sprites using ComfyUI's
controlnet_aux preprocessors (MiDaS for normals, DepthAnything for depth).

Probe directions: front, left, back, right
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

# Source: Kael 1C albedo raws
SOURCE_DIR = FOUNDRY_ROOT / "bakeoff" / "kael_1c_20260326_033800"

# Probe directions only
PROBE_DIRS = ["front", "left", "back", "right"]

# Output
OUTPUT_DIR = FOUNDRY_ROOT / "bakeoff" / "kael_1c_maps"


def make_normal_workflow(image_filename: str) -> dict:
    """Derive normal map using MiDaS Normal preprocessor."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
        },
        "2": {
            "class_type": "MiDaS-NormalMapPreprocessor",
            "inputs": {
                "image": ["1", 0],
                "a": 6.283185307179586,  # 2*pi — standard
                "bg_threshold": 0.1,
                "resolution": 768,
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["2", 0],
                "filename_prefix": "kael_normal",
            },
        },
    }


def make_depth_workflow(image_filename: str) -> dict:
    """Derive depth map using DepthAnything preprocessor."""
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": image_filename},
        },
        "2": {
            "class_type": "DepthAnythingPreprocessor",
            "inputs": {
                "image": ["1", 0],
                "ckpt_name": "depth_anything_vitl14.pth",
                "resolution": 768,
            },
        },
        "3": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["2", 0],
                "filename_prefix": "kael_depth",
            },
        },
    }


def queue_prompt(workflow):
    data = json.dumps({"prompt": workflow}).encode()
    req = Request(f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        return json.loads(resp.read())


def wait_for_completion(prompt_id, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urlopen(f"{COMFY_URL}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError(f"Prompt {prompt_id} timed out after {timeout}s")


def get_image(filename, subfolder=""):
    params = f"filename={filename}&subfolder={subfolder}&type=output"
    with urlopen(f"{COMFY_URL}/view?{params}") as resp:
        return resp.read()


def upload_image(filepath: Path) -> str:
    """Upload an image to ComfyUI's input folder and return the filename."""
    import mimetypes
    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    filename = filepath.name
    mime = mimetypes.guess_type(str(filepath))[0] or "image/png"

    with open(filepath, "rb") as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"image\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    req = Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(req) as resp:
        result = json.loads(resp.read())
    return result["name"]


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


def make_review_sheet(results, output_path):
    """3-row review: albedo, normal, depth across probe directions."""
    CELL = 160
    PAD = 4
    LABEL_W = 80
    HEADER_H = 28
    CELL_W = CELL + PAD * 2
    CELL_H = int(CELL * 768 / 576) + PAD * 2  # portrait aspect
    BG = (24, 24, 32)
    TEXT = (200, 200, 210)
    ACCENT = (120, 160, 200)
    GRID = (50, 50, 60)

    cols = len(PROBE_DIRS)
    rows = 3  # albedo, normal, depth
    row_labels = ["Albedo", "Normal", "Depth"]

    total_w = LABEL_W + cols * CELL_W + 20
    total_h = 10 + 24 + HEADER_H + rows * CELL_H + 10 + 40
    img = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_sm = ImageFont.truetype("consola.ttf", 11)
        font_md = ImageFont.truetype("consola.ttf", 13)
        font_lg = ImageFont.truetype("consola.ttf", 15)
    except (OSError, IOError):
        font_sm = font_md = font_lg = ImageFont.load_default()

    ox, oy = 10, 10
    draw.text((ox, oy), "Phase 1C.2 — Kael Morrow Map Probe", fill=ACCENT, font=font_lg)
    oy += 24

    for col, dir_name in enumerate(PROBE_DIRS):
        draw.text((ox + LABEL_W + col * CELL_W + PAD, oy + 2), dir_name, fill=TEXT, font=font_sm)
    oy += HEADER_H

    cell_h_inner = int(CELL * 768 / 576)

    for row_idx, label in enumerate(row_labels):
        ry = oy + row_idx * CELL_H
        draw.text((ox + 4, ry + cell_h_inner // 2 - 6), label, fill=ACCENT, font=font_md)

        for col, dir_name in enumerate(PROBE_DIRS):
            cx = ox + LABEL_W + col * CELL_W + PAD
            cy = ry + PAD

            if row_idx == 0:
                key = f"{dir_name}_albedo"
            elif row_idx == 1:
                key = f"{dir_name}_normal"
            else:
                key = f"{dir_name}_depth"

            if key in results and results[key] is not None:
                thumb = results[key].resize((CELL, cell_h_inner), Image.LANCZOS)
                if thumb.mode == "RGBA":
                    bg_rect = Image.new("RGB", (CELL, cell_h_inner), (40, 40, 50))
                    bg_rect.paste(thumb, (0, 0), thumb)
                    img.paste(bg_rect, (cx, cy))
                else:
                    img.paste(thumb.convert("RGB"), (cx, cy))
            else:
                draw.rectangle([cx, cy, cx + CELL, cy + cell_h_inner], fill=(60, 30, 30), outline=GRID)
                draw.text((cx + 10, cy + cell_h_inner // 2 - 6), "MISSING", fill=(200, 80, 80), font=font_sm)

    fy = oy + rows * CELL_H + 10
    draw.line([(ox, fy), (total_w - 10, fy)], fill=GRID)
    fy += 6
    draw.text((ox, fy), "Probe: front, left, back, right | MiDaS normals + DepthAnything depth", fill=TEXT, font=font_sm)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def run():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for dir_name in PROBE_DIRS:
        raw_path = SOURCE_DIR / f"{dir_name}_raw.png"
        if not raw_path.exists():
            print(f"  [{dir_name}] SKIP — raw not found: {raw_path}")
            continue

        # Store albedo for review
        results[f"{dir_name}_albedo"] = Image.open(raw_path)

        # Upload raw to ComfyUI
        print(f"  [{dir_name}] uploading raw...", end=" ", flush=True)
        uploaded_name = upload_image(raw_path)
        print(f"as '{uploaded_name}'")

        # Normal map
        print(f"  [{dir_name}] normal map...", end=" ", flush=True)
        try:
            wf = make_normal_workflow(uploaded_name)
            resp = queue_prompt(wf)
            pid = resp["prompt_id"]
            history = wait_for_completion(pid)
            img_info = history["outputs"]["3"]["images"][0]
            img_data = get_image(img_info["filename"], img_info.get("subfolder", ""))

            normal_raw_path = OUTPUT_DIR / f"{dir_name}_normal_raw.png"
            with open(normal_raw_path, "wb") as f:
                f.write(img_data)

            normal_raw = Image.open(normal_raw_path)
            results[f"{dir_name}_normal"] = normal_raw

            # Pixelate normal to 48x48
            w, h = normal_raw.size
            if h > w:
                top = (h - w) // 4
                cropped = normal_raw.crop((0, top, w, top + w))
            else:
                cropped = normal_raw
            normal_px = cropped.resize((SPRITE_TARGET, SPRITE_TARGET), Image.NEAREST)
            normal_px.save(str(OUTPUT_DIR / f"{dir_name}_normal.png"))
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
            results[f"{dir_name}_normal"] = None

        # Depth map
        print(f"  [{dir_name}] depth map...", end=" ", flush=True)
        try:
            wf = make_depth_workflow(uploaded_name)
            resp = queue_prompt(wf)
            pid = resp["prompt_id"]
            history = wait_for_completion(pid)
            img_info = history["outputs"]["3"]["images"][0]
            img_data = get_image(img_info["filename"], img_info.get("subfolder", ""))

            depth_raw_path = OUTPUT_DIR / f"{dir_name}_depth_raw.png"
            with open(depth_raw_path, "wb") as f:
                f.write(img_data)

            depth_raw = Image.open(depth_raw_path)
            results[f"{dir_name}_depth"] = depth_raw

            # Pixelate depth to 48x48
            w, h = depth_raw.size
            if h > w:
                top = (h - w) // 4
                cropped = depth_raw.crop((0, top, w, top + w))
            else:
                cropped = depth_raw
            depth_px = cropped.resize((SPRITE_TARGET, SPRITE_TARGET), Image.NEAREST)
            depth_px.save(str(OUTPUT_DIR / f"{dir_name}_depth.png"))
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
            results[f"{dir_name}_depth"] = None

    # Review sheet
    review_path = OUTPUT_DIR / "kael_map_probe_review.png"
    make_review_sheet(results, review_path)
    print(f"\n  Review sheet: {review_path}")

    # Count successes
    normals = sum(1 for d in PROBE_DIRS if results.get(f"{d}_normal") is not None)
    depths = sum(1 for d in PROBE_DIRS if results.get(f"{d}_depth") is not None)
    print(f"  Normals: {normals}/{len(PROBE_DIRS)}")
    print(f"  Depths: {depths}/{len(PROBE_DIRS)}")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    run()
