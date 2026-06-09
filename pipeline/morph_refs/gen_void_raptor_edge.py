"""Generate Canny-style edge reference images for Void Raptor wing control.

White lines on black background — explicit wing contour edges that
ControlNet Canny will enforce during generation.

Designed to complement the depth silhouette refs. Depth controls body mass,
Canny controls wing edge placement and fold state.

All wings are drawn FOLDED (tight against back) in every direction.
"""

from PIL import Image, ImageDraw
from pathlib import Path

OUT_DIR = Path(__file__).parent / "void_raptor_edge"
GEN_WIDTH = 576
GEN_HEIGHT = 768

# Line properties
EDGE_WIDTH = 5  # thick enough to survive Canny detection
EDGE_COLOR = 255  # white on black


def _soften(img):
    """Light blur to make edges slightly softer (more natural for Canny)."""
    small = img.resize((GEN_WIDTH // 2, GEN_HEIGHT // 2), Image.LANCZOS)
    return small.resize((GEN_WIDTH, GEN_HEIGHT), Image.LANCZOS)


def draw_edge_ref(direction: str) -> Image.Image:
    img = Image.new("L", (GEN_WIDTH, GEN_HEIGHT), 0)
    draw = ImageDraw.Draw(img)

    cx, cy = GEN_WIDTH / 2, GEN_HEIGHT * 0.45

    # Body dimensions (match depth refs)
    bw = GEN_WIDTH * 0.22
    bh = GEN_HEIGHT * 0.22
    hw = GEN_WIDTH * 0.12
    hh = GEN_HEIGHT * 0.08
    lh = GEN_HEIGHT * 0.20

    # Folded wing dimensions — tight against body
    wing_w = GEN_WIDTH * 0.10  # narrow when folded
    wing_h = GEN_HEIGHT * 0.26

    if direction in ("front", "back"):
        # Body outline
        draw.ellipse([cx-bw/2, cy-bh/2, cx+bw/2, cy+bh/2], outline=EDGE_COLOR, width=EDGE_WIDTH)

        # Folded wings — narrow triangular shapes tight against body sides
        # Left wing
        _draw_folded_wing(draw, cx - bw/2, cy - bh*0.3, -wing_w, wing_h, EDGE_WIDTH)
        # Right wing
        _draw_folded_wing(draw, cx + bw/2, cy - bh*0.3, wing_w, wing_h, EDGE_WIDTH)

        if direction == "front":
            # Neck + head outline
            draw.line([(cx-8, cy-bh/2), (cx-8, cy-bh/2-hh*1.5)], fill=EDGE_COLOR, width=EDGE_WIDTH)
            draw.line([(cx+8, cy-bh/2), (cx+8, cy-bh/2-hh*1.5)], fill=EDGE_COLOR, width=EDGE_WIDTH)
            # Angular head
            draw.polygon([(cx, cy-bh/2-hh*2.2), (cx-hw/2, cy-bh/2-hh*0.8),
                          (cx+hw/2, cy-bh/2-hh*0.8)], outline=EDGE_COLOR, width=EDGE_WIDTH)

        # Leg outlines
        leg_w = bw * 0.25
        for lx in [cx-bw*0.3, cx+bw*0.3]:
            draw.rectangle([lx-leg_w/2, cy+bh/2, lx+leg_w/2, cy+bh/2+lh*0.5], outline=EDGE_COLOR, width=EDGE_WIDTH)
            draw.rectangle([lx-leg_w*0.35, cy+bh/2+lh*0.4, lx+leg_w*0.35, cy+bh/2+lh], outline=EDGE_COLOR, width=EDGE_WIDTH)

    elif direction in ("left", "right"):
        facing_left = direction == "left"
        sign = -1 if facing_left else 1

        # Body outline
        draw.ellipse([cx-bw/2, cy-bh/2, cx+bw/2, cy+bh/2], outline=EDGE_COLOR, width=EDGE_WIDTH)

        # Folded wing (one visible, overlapping body back)
        wing_start = cx + sign * bw * 0.1
        _draw_folded_wing_side(draw, wing_start, cy - bh*0.35, sign * wing_w * 0.5, wing_h, EDGE_WIDTH)

        # Head on neck
        hcx = cx - sign * bw * 0.3
        draw.line([(hcx, cy-bh/2), (hcx, cy-bh/2-hh*1.5)], fill=EDGE_COLOR, width=EDGE_WIDTH)
        draw.polygon([(hcx-sign*hw*0.4, cy-bh/2-hh*2.2), (hcx-hw*0.3, cy-bh/2-hh*0.8),
                      (hcx+hw*0.3, cy-bh/2-hh*0.8)], outline=EDGE_COLOR, width=EDGE_WIDTH)

        # Legs
        leg_w = bw * 0.2
        lx = cx
        draw.rectangle([lx-leg_w/2, cy+bh/2, lx+leg_w/2, cy+bh/2+lh*0.5], outline=EDGE_COLOR, width=EDGE_WIDTH)
        draw.rectangle([lx-leg_w*0.3, cy+bh/2+lh*0.4, lx+leg_w*0.3, cy+bh/2+lh], outline=EDGE_COLOR, width=EDGE_WIDTH)

    else:  # 3/4 views
        facing_left = "left" in direction
        show_front = "front" in direction
        sign = -1 if facing_left else 1

        # Body outline
        draw.ellipse([cx-bw/2-sign*8, cy-bh/2, cx+bw/2-sign*8, cy+bh/2], outline=EDGE_COLOR, width=EDGE_WIDTH)

        # Folded wing
        ws = cx + sign * bw * 0.15
        _draw_folded_wing_side(draw, ws, cy - bh*0.3, sign * wing_w * 0.4, wing_h * 0.9, EDGE_WIDTH)

        if show_front:
            hcx = cx - sign * bw * 0.2
            draw.line([(hcx, cy-bh/2), (hcx, cy-bh/2-hh*1.3)], fill=EDGE_COLOR, width=EDGE_WIDTH)
            draw.polygon([(hcx-sign*hw*0.3, cy-bh/2-hh*2.0), (hcx-hw*0.25, cy-bh/2-hh*0.7),
                          (hcx+hw*0.25, cy-bh/2-hh*0.7)], outline=EDGE_COLOR, width=EDGE_WIDTH)

        # Legs
        leg_w = bw * 0.2
        for off in [-0.15, 0.15]:
            lx = cx + bw * off - sign*5
            draw.rectangle([lx-leg_w/2, cy+bh/2, lx+leg_w/2, cy+bh/2+lh*0.5], outline=EDGE_COLOR, width=EDGE_WIDTH)
            draw.rectangle([lx-leg_w*0.3, cy+bh/2+lh*0.4, lx+leg_w*0.3, cy+bh/2+lh], outline=EDGE_COLOR, width=EDGE_WIDTH)

    return _soften(img)


def _draw_folded_wing(draw, anchor_x, anchor_y, width, height, line_w):
    """Draw a folded wing as a narrow elongated triangle pointing down, front/back view."""
    points = [
        (anchor_x, anchor_y),                          # top attachment
        (anchor_x + width, anchor_y + height * 0.4),   # outer tip
        (anchor_x + width * 0.3, anchor_y + height),   # bottom fold
        (anchor_x, anchor_y + height * 0.8),            # body attachment bottom
    ]
    draw.polygon(points, outline=EDGE_COLOR, width=line_w)


def _draw_folded_wing_side(draw, anchor_x, anchor_y, width, height, line_w):
    """Draw a folded wing from side view — narrow vertical shape on back."""
    points = [
        (anchor_x, anchor_y),                          # top
        (anchor_x + width, anchor_y + height * 0.3),   # slight outward bulge
        (anchor_x + width * 0.5, anchor_y + height),   # bottom tip
        (anchor_x, anchor_y + height * 0.7),            # back against body
    ]
    draw.polygon(points, outline=EDGE_COLOR, width=line_w)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    directions = [
        "front", "front_left", "left", "back_left",
        "back", "back_right", "right", "front_right",
    ]

    for d in directions:
        img = draw_edge_ref(d)
        path = OUT_DIR / f"{d}_edge_ref.png"
        img.save(str(path))
        print(f"  {d}: {path}")

    # Contact sheet
    CELL = 192
    PAD = 4
    sheet_w = len(directions) * (CELL + PAD) + PAD
    sheet_h = CELL + PAD * 2 + 20
    sheet = Image.new("L", (sheet_w, sheet_h), 0)

    for i, d in enumerate(directions):
        ref = Image.open(OUT_DIR / f"{d}_edge_ref.png")
        w, h = ref.size
        top = (h - w) // 4
        cropped = ref.crop((0, top, w, top + w))
        cell = cropped.resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(cell, (PAD + i * (CELL + PAD), PAD + 20))

    sheet.save(str(OUT_DIR / "edge_ref_sheet.png"))
    print(f"\n  Contact sheet: {OUT_DIR / 'edge_ref_sheet.png'}")


if __name__ == "__main__":
    main()
