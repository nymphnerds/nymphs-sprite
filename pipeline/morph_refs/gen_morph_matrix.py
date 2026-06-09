"""Generate depth reference silhouettes for Phase 5B morphology matrix.

Three body families:
1. Skitter Drone — 6-legged arthropod, flat and wide
2. Cargo Beast — heavy quadruped pack animal, ox bulk
3. Void Raptor — tall digitigrade with folded wings
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


# ── Skitter Drone: 6-legged, flat, wide ──────────────────

def draw_skitter(direction):
    img = Image.new("L", (GEN_WIDTH, GEN_HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    cx, cy = GEN_WIDTH / 2, GEN_HEIGHT * 0.55

    bw = GEN_WIDTH * 0.50  # wide body
    bh = GEN_HEIGHT * 0.12  # very flat
    lh = GEN_HEIGHT * 0.10  # short legs
    hw = GEN_WIDTH * 0.12   # small head
    hh = GEN_HEIGHT * 0.08

    if direction in ("front", "back"):
        # Wide flat body, 6 legs spread
        draw.ellipse([cx-bw/2, cy-bh/2, cx+bw/2, cy+bh/2], fill=190)
        if direction == "front":
            # Head/mandibles
            draw.ellipse([cx-hw/2, cy-bh/2-hh*0.5, cx+hw/2, cy-bh/2+hh*0.5], fill=220)
            # Antennae stubs
            draw.line([(cx-hw*0.3, cy-bh/2-hh*0.5), (cx-hw*0.6, cy-bh/2-hh*1.2)], fill=180, width=4)
            draw.line([(cx+hw*0.3, cy-bh/2-hh*0.5), (cx+hw*0.6, cy-bh/2-hh*1.2)], fill=180, width=4)
        # 6 legs
        leg_w = bw * 0.08
        for lx in [cx-bw*0.42, cx-bw*0.22, cx-bw*0.02, cx+bw*0.02, cx+bw*0.22, cx+bw*0.42]:
            draw.rectangle([lx-leg_w/2, cy+bh/2-3, lx+leg_w/2, cy+bh/2+lh], fill=150)

    elif direction in ("left", "right"):
        facing_left = direction == "left"
        sign = -1 if facing_left else 1
        body_w = bw * 1.0
        draw.ellipse([cx-body_w/2, cy-bh/2, cx+body_w/2, cy+bh/2], fill=190)
        # Head
        hcx = cx - sign * body_w * 0.45
        draw.ellipse([hcx-hw*0.5, cy-bh*0.4-hh*0.3, hcx+hw*0.5, cy-bh*0.4+hh*0.5], fill=220)
        # 3 visible legs (side)
        leg_w = bw * 0.07
        for off in [-0.25, 0.0, 0.25]:
            lx = cx + body_w * off
            draw.rectangle([lx-leg_w/2, cy+bh/2-3, lx+leg_w/2, cy+bh/2+lh], fill=150)

    else:  # 3/4 views
        facing_left = "left" in direction
        show_front = "front" in direction
        sign = -1 if facing_left else 1
        body_w = bw * 0.85
        draw.ellipse([cx-body_w/2-sign*15, cy-bh/2, cx+body_w/2-sign*15, cy+bh/2], fill=190)
        if show_front:
            hcx = cx - sign * body_w * 0.3
            draw.ellipse([hcx-hw*0.45, cy-bh*0.4-hh*0.3, hcx+hw*0.45, cy-bh*0.4+hh*0.4], fill=220)
        # 4-5 visible legs
        leg_w = bw * 0.07
        for off in [-0.35, -0.12, 0.08, 0.28]:
            lx = cx + body_w * off - sign*10
            draw.rectangle([lx-leg_w/2, cy+bh/2-3, lx+leg_w/2, cy+bh/2+lh], fill=150)

    return _soften(img)


# ── Cargo Beast: heavy quadruped, ox bulk ─────────────────

def draw_cargo_beast(direction):
    img = Image.new("L", (GEN_WIDTH, GEN_HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    cx, cy = GEN_WIDTH / 2, GEN_HEIGHT * 0.50

    bw = GEN_WIDTH * 0.48  # wide
    bh = GEN_HEIGHT * 0.25  # tall barrel body
    lh = GEN_HEIGHT * 0.18  # long thick legs
    hw = GEN_WIDTH * 0.18   # big head
    hh = GEN_HEIGHT * 0.15
    leg_w = bw * 0.14       # thick legs

    if direction in ("front", "back"):
        # Barrel body
        draw.ellipse([cx-bw/2, cy-bh/2, cx+bw/2, cy+bh/2], fill=200)
        if direction == "front":
            # Big head low
            draw.ellipse([cx-hw/2, cy-bh/2-hh*0.3, cx+hw/2, cy-bh/2+hh*0.6], fill=230)
            # Horns/tusks
            draw.line([(cx-hw*0.4, cy-bh/2-hh*0.1), (cx-hw*0.7, cy-bh/2-hh*0.5)], fill=210, width=6)
            draw.line([(cx+hw*0.4, cy-bh/2-hh*0.1), (cx+hw*0.7, cy-bh/2-hh*0.5)], fill=210, width=6)
        else:
            # Rump, small tail
            draw.ellipse([cx-20, cy-bh/2-30, cx+20, cy-bh/2+10], fill=160)
        # 4 thick legs
        for lx in [cx-bw*0.32, cx-bw*0.1, cx+bw*0.1, cx+bw*0.32]:
            draw.rectangle([lx-leg_w/2, cy+bh/2-8, lx+leg_w/2, cy+bh/2+lh], fill=170)

    elif direction in ("left", "right"):
        facing_left = direction == "left"
        sign = -1 if facing_left else 1
        body_w = bw * 1.15
        draw.ellipse([cx-body_w/2, cy-bh/2, cx+body_w/2, cy+bh/2], fill=200)
        # Head
        hcx = cx - sign * body_w * 0.42
        draw.ellipse([hcx-hw*0.5, cy-bh*0.3-hh*0.2, hcx+hw*0.5, cy-bh*0.3+hh*0.6], fill=230)
        # Horns
        draw.line([(hcx-sign*hw*0.3, cy-bh*0.3-hh*0.1), (hcx-sign*hw*0.7, cy-bh*0.3-hh*0.6)], fill=210, width=5)
        # Tail
        tcx = cx + sign * body_w * 0.45
        draw.ellipse([tcx-15, cy-bh*0.2-20, tcx+15, cy-bh*0.2+10], fill=150)
        # 2 visible legs
        for off in [-0.15, 0.2]:
            lx = cx + body_w * off
            draw.rectangle([lx-leg_w/2, cy+bh/2-8, lx+leg_w/2, cy+bh/2+lh], fill=170)

    else:  # 3/4 views
        facing_left = "left" in direction
        show_front = "front" in direction
        sign = -1 if facing_left else 1
        body_w = bw * 1.0
        draw.ellipse([cx-body_w/2-sign*20, cy-bh/2, cx+body_w/2-sign*20, cy+bh/2], fill=200)
        if show_front:
            hcx = cx - sign * body_w * 0.35
            draw.ellipse([hcx-hw*0.45, cy-bh*0.3-hh*0.2, hcx+hw*0.45, cy-bh*0.3+hh*0.5], fill=230)
            draw.line([(hcx-sign*hw*0.3, cy-bh*0.3-hh*0.1), (hcx-sign*hw*0.6, cy-bh*0.3-hh*0.4)], fill=210, width=5)
        else:
            tcx = cx + sign * body_w * 0.35
            draw.ellipse([tcx-12, cy-bh*0.3-15, tcx+12, cy-bh*0.3+8], fill=150)
        # 3 visible legs
        for off in [-0.25, 0.0, 0.22]:
            lx = cx + body_w * off - sign*12
            draw.rectangle([lx-leg_w/2, cy+bh/2-8, lx+leg_w/2, cy+bh/2+lh], fill=170)

    return _soften(img)


# ── Void Raptor: tall digitigrade, folded wings ───────────

def draw_void_raptor(direction):
    img = Image.new("L", (GEN_WIDTH, GEN_HEIGHT), 0)
    draw = ImageDraw.Draw(img)
    cx, cy = GEN_WIDTH / 2, GEN_HEIGHT * 0.45

    # Tall, narrow, vertical
    bw = GEN_WIDTH * 0.22   # narrow torso
    bh = GEN_HEIGHT * 0.22  # tall torso
    lh = GEN_HEIGHT * 0.20  # long digitigrade legs
    hw = GEN_WIDTH * 0.12   # small angular head
    hh = GEN_HEIGHT * 0.08
    wing_w = GEN_WIDTH * 0.18  # folded wing width per side
    wing_h = GEN_HEIGHT * 0.28

    if direction in ("front", "back"):
        # Narrow torso
        draw.ellipse([cx-bw/2, cy-bh/2, cx+bw/2, cy+bh/2], fill=190)
        # Folded wings (triangular shapes on sides)
        draw.polygon([(cx-bw/2, cy-bh*0.3), (cx-bw/2-wing_w, cy+bh*0.1),
                       (cx-bw/2, cy+bh*0.3)], fill=160)
        draw.polygon([(cx+bw/2, cy-bh*0.3), (cx+bw/2+wing_w, cy+bh*0.1),
                       (cx+bw/2, cy+bh*0.3)], fill=160)
        if direction == "front":
            # Angular head on long neck
            draw.rectangle([cx-8, cy-bh/2-hh*1.5, cx+8, cy-bh/2], fill=180)  # neck
            draw.polygon([(cx, cy-bh/2-hh*2.2), (cx-hw/2, cy-bh/2-hh*0.8),
                          (cx+hw/2, cy-bh/2-hh*0.8)], fill=220)  # angular head
        # Digitigrade legs (backwards knee)
        leg_w = bw * 0.25
        for lx in [cx-bw*0.3, cx+bw*0.3]:
            # Upper leg
            draw.rectangle([lx-leg_w/2, cy+bh/2-5, lx+leg_w/2, cy+bh/2+lh*0.5], fill=170)
            # Lower leg (angled outward slightly)
            draw.rectangle([lx-leg_w*0.35, cy+bh/2+lh*0.4, lx+leg_w*0.35, cy+bh/2+lh], fill=160)

    elif direction in ("left", "right"):
        facing_left = direction == "left"
        sign = -1 if facing_left else 1
        # Torso
        draw.ellipse([cx-bw/2, cy-bh/2, cx+bw/2, cy+bh/2], fill=190)
        # Folded wing (one visible, overlapping body)
        wing_start = cx + sign * bw * 0.1
        draw.polygon([(wing_start, cy-bh*0.35), (wing_start+sign*wing_w*0.6, cy+bh*0.15),
                       (wing_start, cy+bh*0.4)], fill=160)
        # Head on neck
        hcx = cx - sign * bw * 0.3
        draw.rectangle([hcx-6, cy-bh/2-hh*1.5, hcx+6, cy-bh/2], fill=180)
        draw.polygon([(hcx-sign*hw*0.4, cy-bh/2-hh*2.2), (hcx-hw*0.3, cy-bh/2-hh*0.8),
                      (hcx+hw*0.3, cy-bh/2-hh*0.8)], fill=220)
        # Digitigrade legs
        leg_w = bw * 0.2
        lx = cx
        draw.rectangle([lx-leg_w/2, cy+bh/2-5, lx+leg_w/2, cy+bh/2+lh*0.5], fill=170)
        draw.rectangle([lx-leg_w*0.3, cy+bh/2+lh*0.4, lx+leg_w*0.3, cy+bh/2+lh], fill=160)

    else:  # 3/4 views
        facing_left = "left" in direction
        show_front = "front" in direction
        sign = -1 if facing_left else 1
        draw.ellipse([cx-bw/2-sign*8, cy-bh/2, cx+bw/2-sign*8, cy+bh/2], fill=190)
        # Wing
        ws = cx + sign * bw * 0.15
        draw.polygon([(ws, cy-bh*0.3), (ws+sign*wing_w*0.5, cy+bh*0.1),
                       (ws, cy+bh*0.35)], fill=160)
        if show_front:
            hcx = cx - sign * bw * 0.2
            draw.rectangle([hcx-6, cy-bh/2-hh*1.3, hcx+6, cy-bh/2], fill=180)
            draw.polygon([(hcx-sign*hw*0.3, cy-bh/2-hh*2.0), (hcx-hw*0.25, cy-bh/2-hh*0.7),
                          (hcx+hw*0.25, cy-bh/2-hh*0.7)], fill=220)
        # Legs
        leg_w = bw * 0.2
        for off in [-0.15, 0.15]:
            lx = cx + bw * off - sign*5
            draw.rectangle([lx-leg_w/2, cy+bh/2-5, lx+leg_w/2, cy+bh/2+lh*0.5], fill=170)
            draw.rectangle([lx-leg_w*0.3, cy+bh/2+lh*0.4, lx+leg_w*0.3, cy+bh/2+lh], fill=160)

    return _soften(img)


DIRECTIONS = [
    "front", "front_left", "left", "back_left",
    "back", "back_right", "right", "front_right",
]


def gen_set(name, draw_fn):
    out_dir = OUT_BASE / f"{name}_depth"
    out_dir.mkdir(parents=True, exist_ok=True)
    for d in DIRECTIONS:
        img = draw_fn(d)
        img.save(str(out_dir / f"{d}_depth_ref.png"))
    _make_sheet(out_dir, DIRECTIONS)
    print(f"  {name}: {out_dir}")


if __name__ == "__main__":
    print("Generating morphology matrix depth refs...")
    gen_set("skitter_drone", draw_skitter)
    gen_set("cargo_beast", draw_cargo_beast)
    gen_set("void_raptor", draw_void_raptor)
    print("Done.")
