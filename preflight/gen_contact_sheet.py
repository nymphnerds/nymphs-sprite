"""
Generate a placeholder contact sheet for the foundry review loop.

This script produces the canonical review artifact layout:
- Row 1: 8 albedo direction slots
- Row 2: 8 normal map slots
- Row 3: 8 depth map slots
- Metadata block below
- Status/review block below that

Run: python preflight/gen_contact_sheet.py
Output: preflight/contact-sheet-placeholder.png
"""

from PIL import Image, ImageDraw, ImageFont
import os

# --- Config ---
SPRITE_SIZE = 48  # display size per sprite cell
CELL_PAD = 4  # padding around each sprite
COLS = 8  # 8 directions
ROWS = 3  # albedo, normal, depth
DIRECTIONS = ["Front", "F-Left", "Left", "B-Left", "Back", "B-Right", "Right", "F-Right"]
ROW_LABELS = ["Albedo", "Normal", "Depth"]
ROW_COLORS = [
    (60, 60, 80),    # albedo placeholder — dark blue-gray
    (80, 60, 80),    # normal placeholder — dark purple
    (60, 80, 60),    # depth placeholder — dark green
]

# Layout math
LABEL_W = 70  # left label column width
HEADER_H = 24  # top header row height
CELL_W = SPRITE_SIZE + CELL_PAD * 2
CELL_H = SPRITE_SIZE + CELL_PAD * 2
GRID_W = LABEL_W + COLS * CELL_W
GRID_H = HEADER_H + ROWS * CELL_H

# Metadata and status blocks
META_H = 100
STATUS_H = 80
TOTAL_W = GRID_W + 20  # 10px margin each side
TOTAL_H = GRID_H + META_H + STATUS_H + 30  # margins

BG_COLOR = (24, 24, 32)
TEXT_COLOR = (200, 200, 210)
GRID_LINE_COLOR = (50, 50, 60)
ACCENT_COLOR = (120, 160, 200)

MARGIN_X = 10
MARGIN_Y = 10


def get_font(size=12):
    """Try to load a monospace font, fall back to default."""
    try:
        return ImageFont.truetype("consola.ttf", size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("cour.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()


def draw_placeholder_sprite(draw, x, y, w, h, color, label):
    """Draw a placeholder sprite cell with label."""
    draw.rectangle([x, y, x + w - 1, y + h - 1], fill=color, outline=GRID_LINE_COLOR)
    font = get_font(9)
    bbox = draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x + (w - tw) // 2
    ty = y + (h - th) // 2
    draw.text((tx, ty), label, fill=TEXT_COLOR, font=font)


def generate_contact_sheet(output_path):
    img = Image.new("RGB", (TOTAL_W, TOTAL_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    font_sm = get_font(10)
    font_md = get_font(12)
    font_lg = get_font(14)

    ox = MARGIN_X
    oy = MARGIN_Y

    # --- Title ---
    draw.text((ox, oy), "FOUNDRY REVIEW — Contact Sheet", fill=ACCENT_COLOR, font=font_lg)
    oy += 20

    # --- Column headers (directions) ---
    for col in range(COLS):
        cx = ox + LABEL_W + col * CELL_W + CELL_PAD
        draw.text((cx, oy + 4), DIRECTIONS[col], fill=TEXT_COLOR, font=font_sm)
    oy += HEADER_H

    # --- Sprite grid ---
    for row in range(ROWS):
        # Row label
        ry = oy + row * CELL_H + CELL_PAD + (SPRITE_SIZE // 2) - 6
        draw.text((ox + 4, ry), ROW_LABELS[row], fill=ACCENT_COLOR, font=font_md)

        for col in range(COLS):
            cx = ox + LABEL_W + col * CELL_W + CELL_PAD
            cy = oy + row * CELL_H + CELL_PAD
            label = f"{DIRECTIONS[col][:3]}\n{ROW_LABELS[row][:3]}"
            draw_placeholder_sprite(draw, cx, cy, SPRITE_SIZE, SPRITE_SIZE, ROW_COLORS[row], label)

    oy += ROWS * CELL_H + 10

    # --- Separator ---
    draw.line([(ox, oy), (TOTAL_W - MARGIN_X, oy)], fill=GRID_LINE_COLOR, width=1)
    oy += 6

    # --- Metadata block ---
    draw.text((ox, oy), "METADATA", fill=ACCENT_COLOR, font=font_md)
    oy += 16
    meta_lines = [
        "Asset ID:    sera_vale_001",
        "Character:   Sera Vale",
        "Stack:       (pending bakeoff)",
        "Sprite Size: 48x48",
        "Seed:        —",
        "Workflow:    —",
        "Generated:   —",
    ]
    for line in meta_lines:
        draw.text((ox + 8, oy), line, fill=TEXT_COLOR, font=font_sm)
        oy += 13
    oy += 4

    # --- Separator ---
    draw.line([(ox, oy), (TOTAL_W - MARGIN_X, oy)], fill=GRID_LINE_COLOR, width=1)
    oy += 6

    # --- Status/review block ---
    draw.text((ox, oy), "REVIEW STATUS", fill=ACCENT_COLOR, font=font_md)
    oy += 16
    status_lines = [
        "Mechanical:  —",
        "Human:       —",
        "Review Code: —",
        "Predecessor: —",
        "Notes:       (placeholder — no generation run yet)",
    ]
    for line in status_lines:
        draw.text((ox + 8, oy), line, fill=TEXT_COLOR, font=font_sm)
        oy += 13

    img.save(output_path)
    print(f"Contact sheet saved: {output_path}")
    print(f"Dimensions: {img.size[0]}x{img.size[1]}")
    return output_path


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(script_dir, "contact-sheet-placeholder.png")
    generate_contact_sheet(out)
