"""Generate depth reference silhouettes for quadrupedal creatures.

Creates simple depth maps (white=near, black=far) that enforce
a low-slung quadrupedal body plan via ControlNet Depth.

8 directions, matching the foundry's standard direction set.
"""

from PIL import Image, ImageDraw
from pathlib import Path
import math

OUT_DIR = Path(__file__).parent / "drift_maw_depth"
GEN_WIDTH = 576
GEN_HEIGHT = 768

# Body proportions (relative to frame)
BODY_W = 0.55   # body width as fraction of frame width
BODY_H = 0.18   # body height (low, flat)
LEG_H = 0.12    # leg height
HEAD_W = 0.18   # head/jaw width
HEAD_H = 0.14   # head height
TAIL_W = 0.20   # tail length
TAIL_H = 0.06   # tail thickness

# Vertical center — creature sits in lower-center of portrait frame
CENTER_Y = 0.55  # slightly below center (portrait aspect)


def draw_quadruped_depth(direction: str) -> Image.Image:
    """Draw a depth-map silhouette for one direction.

    Uses simple shapes: ellipses for body/head, rectangles for legs,
    with depth gradients (white=near, black=far).
    """
    img = Image.new("L", (GEN_WIDTH, GEN_HEIGHT), 0)  # black background
    draw = ImageDraw.Draw(img)

    cx = GEN_WIDTH / 2
    cy = GEN_HEIGHT * CENTER_Y

    bw = GEN_WIDTH * BODY_W
    bh = GEN_HEIGHT * BODY_H
    lh = GEN_HEIGHT * LEG_H
    hw = GEN_WIDTH * HEAD_W
    hh = GEN_HEIGHT * HEAD_H
    tw = GEN_WIDTH * TAIL_W
    th = GEN_HEIGHT * TAIL_H

    # Direction offsets — shift head/tail laterally for angle views
    # front: head centered, body wide
    # side: head at one end, tail at other, body narrower (profile)
    # back: tail visible, head hidden

    if direction == "front":
        _draw_front(draw, cx, cy, bw, bh, lh, hw, hh)
    elif direction == "back":
        _draw_back(draw, cx, cy, bw, bh, lh, tw, th)
    elif direction == "left":
        _draw_side(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left=True)
    elif direction == "right":
        _draw_side(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left=False)
    elif direction == "front_left":
        _draw_3q(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left=True, show_front=True)
    elif direction == "front_right":
        _draw_3q(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left=False, show_front=True)
    elif direction == "back_left":
        _draw_3q(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left=True, show_front=False)
    elif direction == "back_right":
        _draw_3q(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left=False, show_front=False)

    # Apply gaussian-like softening via resize trick
    small = img.resize((GEN_WIDTH // 4, GEN_HEIGHT // 4), Image.LANCZOS)
    img = small.resize((GEN_WIDTH, GEN_HEIGHT), Image.LANCZOS)

    return img


def _draw_front(draw, cx, cy, bw, bh, lh, hw, hh):
    """Front view: wide body, head centered above, 4 legs below."""
    # Body (ellipse, wide and flat) — near depth (bright)
    draw.ellipse([cx - bw/2, cy - bh/2, cx + bw/2, cy + bh/2], fill=200)

    # Head/jaw (centered, slightly above body) — nearest (brightest)
    draw.ellipse([cx - hw/2, cy - bh/2 - hh*0.6, cx + hw/2, cy - bh/2 + hh*0.4], fill=240)
    # Jaw extension (oval below head)
    draw.ellipse([cx - hw*0.4, cy - bh/2 - hh*0.1, cx + hw*0.4, cy - bh/2 + hh*0.6], fill=230)

    # 4 legs (slightly spread) — medium depth
    leg_w = bw * 0.12
    for lx in [cx - bw*0.38, cx - bw*0.15, cx + bw*0.15, cx + bw*0.38]:
        draw.rectangle([lx - leg_w/2, cy + bh/2 - 5, lx + leg_w/2, cy + bh/2 + lh], fill=160)


def _draw_back(draw, cx, cy, bw, bh, lh, tw, th):
    """Back view: wide body, tail visible, no head."""
    # Body
    draw.ellipse([cx - bw/2, cy - bh/2, cx + bw/2, cy + bh/2], fill=180)

    # Dorsal ridge (small bumps along top)
    for i in range(5):
        rx = cx - bw*0.25 + i * bw*0.125
        draw.ellipse([rx - 8, cy - bh/2 - 12, rx + 8, cy - bh/2 + 4], fill=190)

    # Tail (curving up from back) — medium depth
    draw.ellipse([cx - tw*0.3, cy - bh/2 - th*2, cx + tw*0.3, cy - bh/2 + th], fill=150)

    # 4 legs
    leg_w = bw * 0.12
    for lx in [cx - bw*0.38, cx - bw*0.15, cx + bw*0.15, cx + bw*0.38]:
        draw.rectangle([lx - leg_w/2, cy + bh/2 - 5, lx + leg_w/2, cy + bh/2 + lh], fill=140)


def _draw_side(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left):
    """Side profile: long horizontal body, head at one end, tail at other."""
    sign = -1 if facing_left else 1

    # Body (longer horizontally in profile)
    body_w = bw * 1.1
    draw.ellipse([cx - body_w/2, cy - bh/2, cx + body_w/2, cy + bh/2], fill=190)

    # Head/jaw at front
    head_cx = cx - sign * body_w * 0.45
    draw.ellipse([head_cx - hw*0.6, cy - bh/2 - hh*0.3, head_cx + hw*0.6, cy - bh/2 + hh*0.7], fill=230)
    # Jaw extension forward
    jaw_cx = head_cx - sign * hw * 0.5
    draw.ellipse([jaw_cx - hw*0.35, cy - hh*0.1, jaw_cx + hw*0.35, cy + hh*0.4], fill=220)

    # Tail at back
    tail_cx = cx + sign * body_w * 0.5
    draw.ellipse([tail_cx - tw*0.4, cy - bh*0.3 - th, tail_cx + tw*0.4, cy - bh*0.3 + th], fill=140)

    # 2 visible legs (side view shows 2)
    leg_w = bw * 0.1
    for lx_offset in [-0.2, 0.2]:
        lx = cx + body_w * lx_offset
        draw.rectangle([lx - leg_w/2, cy + bh/2 - 5, lx + leg_w/2, cy + bh/2 + lh], fill=160)


def _draw_3q(draw, cx, cy, bw, bh, lh, hw, hh, tw, th, facing_left, show_front):
    """3/4 view: between front/side or back/side."""
    sign = -1 if facing_left else 1
    front_sign = -1 if show_front else 1

    # Body (slightly rotated — asymmetric width)
    body_w = bw * 0.9
    draw.ellipse([cx - body_w/2 - sign*20, cy - bh/2, cx + body_w/2 - sign*20, cy + bh/2], fill=190)

    if show_front:
        # Head visible
        head_cx = cx - sign * body_w * 0.3
        draw.ellipse([head_cx - hw*0.5, cy - bh/2 - hh*0.4, head_cx + hw*0.5, cy - bh/2 + hh*0.5], fill=230)
        jaw_cx = head_cx - sign * hw * 0.3
        draw.ellipse([jaw_cx - hw*0.3, cy - hh*0.05, jaw_cx + hw*0.3, cy + hh*0.35], fill=220)
    else:
        # Tail visible
        tail_cx = cx + sign * body_w * 0.35
        draw.ellipse([tail_cx - tw*0.35, cy - bh*0.4 - th, tail_cx + tw*0.35, cy - bh*0.4 + th], fill=140)
        # Dorsal bumps
        for i in range(3):
            rx = cx - sign*10 + i * 25 * (-sign)
            draw.ellipse([rx - 6, cy - bh/2 - 10, rx + 6, cy - bh/2 + 3], fill=170)

    # 3 visible legs (3/4 view)
    leg_w = bw * 0.1
    for lx_offset in [-0.3, 0.0, 0.25]:
        lx = cx + body_w * lx_offset - sign*15
        draw.rectangle([lx - leg_w/2, cy + bh/2 - 5, lx + leg_w/2, cy + bh/2 + lh], fill=160)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    directions = [
        "front", "front_left", "left", "back_left",
        "back", "back_right", "right", "front_right",
    ]

    for d in directions:
        img = draw_quadruped_depth(d)
        path = OUT_DIR / f"{d}_depth_ref.png"
        img.save(str(path))
        print(f"  {d}: {path}")

    # Also make a contact sheet
    CELL = 192
    PAD = 4
    sheet_w = len(directions) * (CELL + PAD) + PAD
    sheet_h = CELL + PAD * 2 + 20
    sheet = Image.new("L", (sheet_w, sheet_h), 0)

    for i, d in enumerate(directions):
        ref = Image.open(OUT_DIR / f"{d}_depth_ref.png")
        # Crop to square center and resize
        w, h = ref.size
        top = (h - w) // 4
        cropped = ref.crop((0, top, w, top + w))
        cell = cropped.resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(cell, (PAD + i * (CELL + PAD), PAD + 20))

    sheet_path = OUT_DIR / "depth_ref_sheet.png"
    sheet.save(str(sheet_path))
    print(f"\n  Contact sheet: {sheet_path}")


if __name__ == "__main__":
    main()
