"""Generate depth reference silhouettes for Keth Healer-Drone.

Body plan: small rounded arthropod, 6 short folded legs, two thin
medical manipulators underneath, rounded carapace (beetle-like but
rounder and smaller than Skitter Drone). Non-threatening medical shape.
"""

from PIL import Image, ImageDraw
from pathlib import Path

OUT_BASE = Path(__file__).parent
GEN_WIDTH = 576
GEN_HEIGHT = 768


def _soften(img):
    small = img.resize((GEN_WIDTH // 4, GEN_HEIGHT // 4), Image.LANCZOS)
    return small.resize((GEN_WIDTH, GEN_HEIGHT), Image.LANCZOS)


def _make_sheet(out_dir, directions):
    CELL = 192
    PAD = 4
    sheet_w = len(directions) * (CELL + PAD) + PAD
    sheet_h = CELL + PAD * 2 + 20
    sheet = Image.new("L", (sheet_w, sheet_h), 0)
    for i, d in enumerate(directions):
        ref = Image.open(out_dir / f"{d}_depth_ref.png")
        w, h = ref.size
        top = (h - w) // 4
        cropped = ref.crop((0, top, w, top + w))
        cell = cropped.resize((CELL, CELL), Image.LANCZOS)
        sheet.paste(cell, (PAD + i * (CELL + PAD), PAD + 20))
    sheet.save(str(out_dir / "depth_ref_sheet.png"))


def draw_healer_drone(direction):
    img = Image.new("L", (GEN_WIDTH, GEN_HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    cx, cy = GEN_WIDTH / 2, GEN_HEIGHT * 0.55

    # Rounded body — wider than tall but not as flat as Skitter
    bw = GEN_WIDTH * 0.35   # moderately wide
    bh = GEN_HEIGHT * 0.16  # rounder than Skitter (0.12)
    lh = GEN_HEIGHT * 0.06  # very short folded legs
    hw = GEN_WIDTH * 0.10   # small delicate head
    hh = GEN_HEIGHT * 0.06
    manip_len = GEN_HEIGHT * 0.08  # thin medical manipulators

    if direction in ("front", "back"):
        # Rounded dome body
        draw.ellipse([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], fill=200)
        # Slightly raised wing covers on top (subtle dome highlight)
        draw.ellipse([cx - bw * 0.3, cy - bh * 0.6, cx + bw * 0.3, cy - bh * 0.1], fill=220)
        if direction == "front":
            # Small head with antennae
            draw.ellipse([cx - hw / 2, cy - bh / 2 - hh * 0.3, cx + hw / 2, cy - bh / 2 + hh * 0.5], fill=230)
            # Two thin forward-curving antennae
            draw.line([(cx - hw * 0.25, cy - bh / 2 - hh * 0.3), (cx - hw * 0.5, cy - bh / 2 - hh * 1.2)], fill=180, width=3)
            draw.line([(cx + hw * 0.25, cy - bh / 2 - hh * 0.3), (cx + hw * 0.5, cy - bh / 2 - hh * 1.2)], fill=180, width=3)
            # Two thin manipulators visible underneath
            draw.line([(cx - bw * 0.08, cy + bh / 2), (cx - bw * 0.15, cy + bh / 2 + manip_len)], fill=160, width=3)
            draw.line([(cx + bw * 0.08, cy + bh / 2), (cx + bw * 0.15, cy + bh / 2 + manip_len)], fill=160, width=3)
        # 6 short folded legs
        leg_w = bw * 0.06
        for lx in [cx - bw * 0.38, cx - bw * 0.18, cx + bw * 0.02,
                    cx - bw * 0.02, cx + bw * 0.18, cx + bw * 0.38]:
            draw.rectangle([lx - leg_w / 2, cy + bh / 2 - 2, lx + leg_w / 2, cy + bh / 2 + lh], fill=150)

    elif direction in ("left", "right"):
        facing_left = direction == "left"
        sign = -1 if facing_left else 1
        body_w = bw * 0.9
        # Rounded dome from side
        draw.ellipse([cx - body_w / 2, cy - bh / 2, cx + body_w / 2, cy + bh / 2], fill=200)
        draw.ellipse([cx - body_w * 0.25, cy - bh * 0.65, cx + body_w * 0.25, cy - bh * 0.05], fill=220)
        # Head
        hcx = cx - sign * body_w * 0.4
        draw.ellipse([hcx - hw * 0.4, cy - bh * 0.3 - hh * 0.2, hcx + hw * 0.4, cy - bh * 0.3 + hh * 0.4], fill=230)
        # Antenna
        draw.line([(hcx - sign * hw * 0.2, cy - bh * 0.3 - hh * 0.2),
                   (hcx - sign * hw * 0.6, cy - bh * 0.3 - hh * 1.0)], fill=180, width=3)
        # 3 visible legs (side)
        leg_w = bw * 0.05
        for off in [-0.2, 0.0, 0.2]:
            lx = cx + body_w * off
            draw.rectangle([lx - leg_w / 2, cy + bh / 2 - 2, lx + leg_w / 2, cy + bh / 2 + lh], fill=150)
        # One visible manipulator
        draw.line([(cx, cy + bh / 2), (cx + sign * bw * 0.05, cy + bh / 2 + manip_len)], fill=160, width=3)

    else:  # 3/4 views
        facing_left = "left" in direction
        show_front = "front" in direction
        sign = -1 if facing_left else 1
        body_w = bw * 0.8
        draw.ellipse([cx - body_w / 2 - sign * 10, cy - bh / 2,
                       cx + body_w / 2 - sign * 10, cy + bh / 2], fill=200)
        draw.ellipse([cx - body_w * 0.22 - sign * 10, cy - bh * 0.6,
                       cx + body_w * 0.22 - sign * 10, cy - bh * 0.05], fill=220)
        if show_front:
            hcx = cx - sign * body_w * 0.28
            draw.ellipse([hcx - hw * 0.35, cy - bh * 0.3 - hh * 0.2,
                          hcx + hw * 0.35, cy - bh * 0.3 + hh * 0.35], fill=230)
            draw.line([(hcx - sign * hw * 0.2, cy - bh * 0.3 - hh * 0.2),
                       (hcx - sign * hw * 0.5, cy - bh * 0.3 - hh * 0.9)], fill=180, width=3)
        # 4 visible legs
        leg_w = bw * 0.05
        for off in [-0.3, -0.1, 0.1, 0.25]:
            lx = cx + body_w * off - sign * 8
            draw.rectangle([lx - leg_w / 2, cy + bh / 2 - 2, lx + leg_w / 2, cy + bh / 2 + lh], fill=150)
        # Manipulator
        if show_front:
            draw.line([(cx - sign * 5, cy + bh / 2),
                       (cx - sign * 10, cy + bh / 2 + manip_len)], fill=160, width=3)

    return _soften(img)


DIRECTIONS = [
    "front", "front_left", "left", "back_left",
    "back", "back_right", "right", "front_right",
]


if __name__ == "__main__":
    out_dir = OUT_BASE / "keth_healer_drone_depth"
    out_dir.mkdir(parents=True, exist_ok=True)
    for d in DIRECTIONS:
        img = draw_healer_drone(d)
        img.save(str(out_dir / f"{d}_depth_ref.png"))
    _make_sheet(out_dir, DIRECTIONS)
    print(f"Keth Healer-Drone depth refs: {out_dir}")
