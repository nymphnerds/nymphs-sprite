"""
Phase 1B.3 — Full 8-Direction Finish Validation Composite
Builds an 8×4 grid: columns = directions, rows = lighting states
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone

SCREENSHOTS = Path(__file__).parent.parent / "game" / "godot" / "render-lab" / "screenshots"
OUTPUT = Path(__file__).parent.parent / "bakeoff" / "phase1b3_composite.png"

DIRECTIONS = ["front", "front_left", "left", "back_left", "back", "back_right", "right", "front_right"]
STATES = ["baseline", "moonlight", "torch", "moon_particles_depth"]
STATE_LABELS = ["Baseline", "Moonlight", "Torch", "Moon+Particles+Depth"]

CELL = 180
PAD = 4
LABEL_W = 140
HEADER_H = 50
BG = (18, 18, 24)
TEXT = (200, 200, 210)
ACCENT = (120, 160, 200)
GRID = (40, 40, 50)

def build():
    cols = len(DIRECTIONS)
    rows = len(STATES)

    total_w = LABEL_W + cols * (CELL + PAD) + 20
    total_h = 60 + HEADER_H + rows * (CELL + PAD) + 80

    img = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(img)

    try:
        font_sm = ImageFont.truetype("consola.ttf", 11)
        font_md = ImageFont.truetype("consola.ttf", 13)
        font_lg = ImageFont.truetype("consola.ttf", 16)
    except (OSError, IOError):
        font_sm = font_md = font_lg = ImageFont.load_default()

    ox, oy = 10, 10
    draw.text((ox, oy), "Phase 1B.3 — 8-Direction Finish Validation", fill=ACCENT, font=font_lg)
    oy += 20
    draw.text((ox, oy), f"Sera Vale | Stack A v2 | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", fill=TEXT, font=font_sm)
    oy += 30

    # Column headers (direction names)
    for col, dir_name in enumerate(DIRECTIONS):
        cx = ox + LABEL_W + col * (CELL + PAD)
        label = dir_name.replace("_", "\n")
        draw.text((cx + PAD, oy), label, fill=TEXT, font=font_sm)
    oy += HEADER_H

    # Grid
    missing = []
    for row, (state, label) in enumerate(zip(STATES, STATE_LABELS)):
        ry = oy + row * (CELL + PAD)
        draw.text((ox + 4, ry + CELL // 2 - 6), label, fill=ACCENT, font=font_md)

        for col, dir_name in enumerate(DIRECTIONS):
            cx = ox + LABEL_W + col * (CELL + PAD)
            png_path = SCREENSHOTS / f"{dir_name}_{state}.png"

            if png_path.exists():
                capture = Image.open(png_path).convert("RGB")
                # Crop to center square if not already square
                w, h = capture.size
                if w != h:
                    side = min(w, h)
                    left = (w - side) // 2
                    top = (h - side) // 2
                    capture = capture.crop((left, top, left + side, top + side))
                display = capture.resize((CELL, CELL), Image.NEAREST)
                img.paste(display, (cx, ry))
            else:
                draw.rectangle([cx, ry, cx + CELL, ry + CELL], fill=(60, 30, 30), outline=GRID)
                draw.text((cx + 10, ry + CELL // 2 - 6), "MISSING", fill=(200, 80, 80), font=font_sm)
                missing.append(f"{dir_name}_{state}")

    # Footer
    fy = oy + rows * (CELL + PAD) + 10
    draw.line([(ox, fy), (total_w - 10, fy)], fill=GRID)
    fy += 8
    status = "COMPLETE — 32/32 captures" if not missing else f"INCOMPLETE — {32 - len(missing)}/32 ({len(missing)} missing)"
    draw.text((ox, fy), status, fill=ACCENT if not missing else (200, 80, 80), font=font_md)
    fy += 18
    draw.text((ox, fy), "Acceptance: silhouette clarity, torch/moon distinct, depth/rim stable, particles non-distracting", fill=TEXT, font=font_sm)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(OUTPUT), "PNG")
    print(f"Composite saved: {OUTPUT}")
    print(f"Size: {total_w}x{total_h}")
    if missing:
        print(f"Missing: {missing}")
    else:
        print("All 32 cells populated.")
    return OUTPUT

if __name__ == "__main__":
    build()
