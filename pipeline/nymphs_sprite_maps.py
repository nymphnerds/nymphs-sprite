"""Model-backed map derivation for Nymphs Sprite outputs.

This replaces the old Foundry ComfyUI map stage with a direct Python path. The
normal map is derived from the selected depth model's depth output. The
alpha-volume backend remains only as an explicit fallback/debug backend.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


DEPTH_ANYTHING_MODEL = "LiheYoung/depth-anything-small-hf"
MIDAS_MODEL = "Intel/dpt-hybrid-midas"

DIRECTIONS_8 = [
    "front",
    "front_left",
    "left",
    "back_left",
    "back",
    "back_right",
    "right",
    "front_right",
]

DIRECTIONS_16 = [
    "front",
    "front_front_left",
    "front_left",
    "left_front_left",
    "left",
    "left_back_left",
    "back_left",
    "back_back_left",
    "back",
    "back_back_right",
    "back_right",
    "right_back_right",
    "right",
    "right_front_right",
    "front_right",
    "front_front_right",
]


def output_root() -> Path:
    return Path.home() / "NymphsData" / "outputs" / "nymphs-sprite"


def huggingface_cache_root() -> Path:
    return Path.home() / "NymphsData" / "cache" / "huggingface"


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def load_font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSansMono.ttf", "consola.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def direction_names(direction_count: int) -> list[str]:
    if direction_count == 16:
        return DIRECTIONS_16
    if direction_count == 8:
        return DIRECTIONS_8
    raise ValueError("direction_count must be 8 or 16")


def existing_direction_images(subject_dir: Path, directions: Iterable[str], source: str) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    if source == "raw":
        search_dir = subject_dir
        suffix = "_raw.png"
    elif source == "cutout":
        search_dir = subject_dir / "_intermediate"
        suffix = "_cutout.png"
    else:
        search_dir = subject_dir
        suffix = ".png"
    for direction in directions:
        path = search_dir / f"{direction}{suffix}"
        if path.is_file():
            paths[direction] = path
    return paths


def nearest_edge_distance(alpha: Image.Image) -> list[list[float]]:
    """Approximate inside distance to the transparent edge using two sweeps."""
    alpha_l = alpha.convert("L")
    width, height = alpha_l.size
    pixels = alpha_l.load()
    foreground = [[pixels[x, y] > 2 for x in range(width)] for y in range(height)]
    if not any(any(row) for row in foreground):
        return [[0.0 for _ in range(width)] for _ in range(height)]

    inf = float(height + width)
    dist = [[inf if foreground[y][x] else 0.0 for x in range(width)] for y in range(height)]
    diag = math.sqrt(2.0)

    for y in range(height):
        for x in range(width):
            best = dist[y][x]
            if y > 0:
                best = min(best, dist[y - 1][x] + 1.0)
                if x > 0:
                    best = min(best, dist[y - 1][x - 1] + diag)
                if x + 1 < width:
                    best = min(best, dist[y - 1][x + 1] + diag)
            if x > 0:
                best = min(best, dist[y][x - 1] + 1.0)
            dist[y][x] = best

    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            best = dist[y][x]
            if y + 1 < height:
                best = min(best, dist[y + 1][x] + 1.0)
                if x > 0:
                    best = min(best, dist[y + 1][x - 1] + diag)
                if x + 1 < width:
                    best = min(best, dist[y + 1][x + 1] + diag)
            if x + 1 < width:
                best = min(best, dist[y][x + 1] + 1.0)
            dist[y][x] = best

    max_dist = max(max(row) for row in dist)
    if max_dist <= 0:
        return [[0.0 for _ in range(width)] for _ in range(height)]
    return [
        [(dist[y][x] / max_dist) if foreground[y][x] else 0.0 for x in range(width)]
        for y in range(height)
    ]


def alpha_volume_depth(image: Image.Image, detail_strength: float = 0.45) -> Image.Image:
    """Generate a depth/height candidate from sprite alpha and luminance.

    This remains a heuristic fallback, but it should preserve visible sprite
    detail instead of becoming only a soft blob.
    """
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    alpha = rgba.getchannel("A")
    edge_distance = nearest_edge_distance(alpha)
    depth_img = Image.new("L", (width, height), 0)
    out = depth_img.load()

    luma_img = ImageOps.grayscale(rgba)
    luma_img = ImageOps.autocontrast(luma_img, cutoff=1)
    luma_img = ImageEnhance.Contrast(luma_img).enhance(1.35)
    luma_px = luma_img.load()
    soft_luma = luma_img.filter(ImageFilter.GaussianBlur(radius=1.25))
    highpass = ImageChops.subtract(luma_img, soft_luma, scale=1.8, offset=96)
    highpass = ImageOps.autocontrast(highpass, cutoff=1)
    high_px = highpass.load()

    lumas: list[float] = []
    for y in range(height):
        for x in range(width):
            _red, _green, _blue, alpha_value = pixels[x, y]
            if alpha_value > 2:
                lumas.append(luma_px[x, y] / 255.0)
    if lumas:
        luma_min = min(lumas)
        luma_max = max(lumas)
    else:
        luma_min = 0.0
        luma_max = 1.0
    luma_range = max(0.001, luma_max - luma_min)
    detail_mix = max(0.0, min(0.85, detail_strength))

    for y in range(height):
        for x in range(width):
            _red, _green, _blue, alpha_value = pixels[x, y]
            if alpha_value <= 2:
                out[x, y] = 0
                continue
            luma = luma_px[x, y] / 255.0
            luma_norm = max(0.0, min(1.0, (luma - luma_min) / luma_range))
            local_detail = high_px[x, y] / 255.0
            volume = math.sqrt(max(0.0, min(1.0, edge_distance[y][x])))
            relief = 0.58 * luma_norm + 0.22 * luma + 0.20 * local_detail
            depth = ((1.0 - detail_mix) * volume + detail_mix * relief) * (alpha_value / 255.0)
            depth = max(0.0, min(1.0, depth))
            out[x, y] = int(depth * 255)

    depth_img = depth_img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=90, threshold=3))
    depth_img = depth_img.filter(ImageFilter.GaussianBlur(radius=0.10))
    return depth_img


def normal_from_depth(depth: Image.Image, alpha: Image.Image, strength: float = 3.0) -> Image.Image:
    depth_l = depth.convert("L")
    alpha_l = alpha.convert("L")
    width, height = depth_l.size
    depth_px = depth_l.load()
    alpha_px = alpha_l.load()
    out = Image.new("RGBA", (width, height), (128, 128, 255, 0))
    out_px = out.load()

    def d(x: int, y: int) -> float:
        x = min(width - 1, max(0, x))
        y = min(height - 1, max(0, y))
        return depth_px[x, y] / 255.0

    for y in range(height):
        for x in range(width):
            gx = (d(x + 1, y) - d(x - 1, y)) * 0.5
            gy = (d(x, y + 1) - d(x, y - 1)) * 0.5
            nx = -gx * strength
            ny = -gy * strength
            nz = 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            red = int((nx / length * 0.5 + 0.5) * 255)
            green = int((ny / length * 0.5 + 0.5) * 255)
            blue = int((nz / length * 0.5 + 0.5) * 255)
            out_px[x, y] = (red, green, blue, alpha_px[x, y])
    return out


def depth_rgba(depth: Image.Image, alpha: Image.Image) -> Image.Image:
    rgba = Image.merge(
        "RGBA",
        (
            depth.convert("L"),
            depth.convert("L"),
            depth.convert("L"),
            alpha.convert("L"),
        ),
    )
    return rgba


def resize_nearest(image: Image.Image, size: int) -> Image.Image:
    return image.convert("RGBA").resize((size, size), Image.Resampling.NEAREST)


def source_for_depth_model(image: Image.Image) -> Image.Image:
    """Composite transparent cutouts for RGB-only depth estimators."""
    rgba = image.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
    bg.alpha_composite(rgba)
    return bg.convert("RGB")


def model_id_for_backend(backend: str, model_id: str | None) -> str:
    if model_id:
        return model_id
    if backend == "depth_anything":
        return DEPTH_ANYTHING_MODEL
    if backend == "midas":
        return MIDAS_MODEL
    raise ValueError(f"backend '{backend}' does not use a model id")


_DEPTH_PIPELINES: dict[tuple[str, str], object] = {}


def get_depth_pipeline(model_id: str, device: str = "auto"):
    """Load/cache a Transformers depth-estimation pipeline."""
    cache_root = huggingface_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_root))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(cache_root / "hub"))

    import torch
    from transformers import pipeline

    if device == "auto":
        resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        resolved_device = device
    hf_device = 0 if resolved_device == "cuda" else -1
    key = (model_id, resolved_device)
    if key not in _DEPTH_PIPELINES:
        kwargs = {}
        if resolved_device == "cuda":
            kwargs["torch_dtype"] = torch.float16
        try:
            _DEPTH_PIPELINES[key] = pipeline(
                task="depth-estimation",
                model=model_id,
                device=hf_device,
                **kwargs,
            )
        except OSError as exc:
            raise RuntimeError(
                f"Could not load depth model '{model_id}'. Fetch it into the shared "
                f"Hugging Face cache first or rerun with network access. Cache: {cache_root}"
            ) from exc
    return _DEPTH_PIPELINES[key]


def normalize_depth(depth: Image.Image, alpha: Image.Image) -> Image.Image:
    """Normalize foreground depth only, preserving transparent background."""
    depth_l = ImageOps.grayscale(depth)
    alpha_l = alpha.convert("L")
    width, height = depth_l.size
    depth_px = depth_l.load()
    alpha_px = alpha_l.load()
    values = [depth_px[x, y] for y in range(height) for x in range(width) if alpha_px[x, y] > 2]
    if not values:
        return Image.new("L", (width, height), 0)

    low = min(values)
    high = max(values)
    if high <= low:
        return Image.new("L", (width, height), 0)

    out = Image.new("L", (width, height), 0)
    out_px = out.load()
    scale = 255.0 / float(high - low)
    for y in range(height):
        for x in range(width):
            if alpha_px[x, y] <= 2:
                continue
            out_px[x, y] = int(max(0, min(255, (depth_px[x, y] - low) * scale)))
    return out


def model_depth(
    image: Image.Image,
    *,
    backend: str,
    model_id: str | None = None,
    device: str = "auto",
) -> Image.Image:
    """Generate depth from Depth Anything or MiDaS through Transformers."""
    resolved_model = model_id_for_backend(backend, model_id)
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    pipe = get_depth_pipeline(resolved_model, device=device)
    result = pipe(source_for_depth_model(rgba))
    depth = result["depth"]
    if not isinstance(depth, Image.Image):
        depth = Image.fromarray(depth)
    if depth.size != rgba.size:
        depth = depth.resize(rgba.size, Image.Resampling.BICUBIC)
    return normalize_depth(depth, alpha)


def make_review_sheet(
    albedo: dict[str, Path],
    depth: dict[str, Path],
    normal: dict[str, Path],
    *,
    directions: list[str],
    out_path: Path,
    title: str,
) -> Path:
    cell = 112
    pad = 10
    label_w = 88
    header_h = 28
    rows = [("Albedo", albedo), ("Depth", depth), ("Normal", normal)]
    cols = [d for d in directions if d in albedo]

    width = label_w + len(cols) * (cell + pad) + pad
    height = 34 + header_h + len(rows) * (cell + pad) + pad
    sheet = Image.new("RGB", (max(width, 360), height), (18, 22, 24))
    draw = ImageDraw.Draw(sheet)
    font_sm = load_font(11)
    font_md = load_font(13)

    draw.text((pad, pad), title, fill=(120, 255, 180), font=font_md)
    y = 34
    for i, direction in enumerate(cols):
        x = label_w + i * (cell + pad)
        draw.text((x, y), direction.replace("_", " "), fill=(185, 210, 210), font=font_sm)
    y += header_h

    for row_idx, (label, mapping) in enumerate(rows):
        row_y = y + row_idx * (cell + pad)
        draw.text((pad, row_y + cell // 2 - 8), label, fill=(92, 255, 240), font=font_md)
        for col_idx, direction in enumerate(cols):
            x = label_w + col_idx * (cell + pad)
            path = mapping.get(direction)
            draw.rectangle((x - 1, row_y - 1, x + cell, row_y + cell), outline=(42, 78, 80))
            if path and path.is_file():
                with Image.open(path) as handle:
                    img = handle.convert("RGBA").resize((cell, cell), Image.Resampling.NEAREST)
                bg = Image.new("RGB", (cell, cell), (4, 8, 8))
                bg.paste(img, (0, 0), img)
                sheet.paste(bg, (x, row_y))
            else:
                draw.text((x + 16, row_y + cell // 2 - 8), "missing", fill=(180, 80, 80), font=font_sm)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, "PNG")
    return out_path


def derive_maps(
    *,
    subject: str,
    input_dir: Path | None = None,
    output_dir: Path | None = None,
    direction_count: int = 8,
    source: str = "cutout",
    backend: str = "depth_anything",
    model_id: str | None = None,
    device: str = "auto",
    sprite_size: int = 96,
    normal_strength: float = 3.0,
    detail_strength: float = 0.45,
) -> dict[str, object]:
    subject_dir = input_dir or output_root() / subject
    if not subject_dir.is_dir():
        raise FileNotFoundError(f"subject output folder not found: {subject_dir}")

    directions = direction_names(direction_count)
    albedo_paths = existing_direction_images(subject_dir, directions, source)
    if not albedo_paths:
        raise FileNotFoundError(f"no {source} direction PNGs found in {subject_dir}")

    map_root = output_dir or subject_dir / "maps" / now_slug()
    normal_dir = map_root / "normal"
    depth_dir = map_root / "depth"
    albedo_dir = map_root / "albedo"
    for path in (normal_dir, depth_dir, albedo_dir):
        path.mkdir(parents=True, exist_ok=True)

    normal_paths: dict[str, Path] = {}
    depth_paths: dict[str, Path] = {}
    copied_albedo: dict[str, Path] = {}

    for direction, source_path in albedo_paths.items():
        with Image.open(source_path) as handle:
            source_image = handle.convert("RGBA")
        native_alpha = source_image.getchannel("A")
        if backend == "alpha_volume":
            native_depth = alpha_volume_depth(source_image, detail_strength=detail_strength)
            resolved_model_id = None
        else:
            native_depth = model_depth(source_image, backend=backend, model_id=model_id, device=device)
            resolved_model_id = model_id_for_backend(backend, model_id)
        native_depth_out = depth_rgba(native_depth, native_alpha)
        native_normal_out = normal_from_depth(native_depth, native_alpha, strength=normal_strength)

        image = resize_nearest(source_image, sprite_size)
        depth_out = resize_nearest(native_depth_out, sprite_size)
        normal_out = resize_nearest(native_normal_out, sprite_size)

        albedo_path = albedo_dir / f"{direction}.png"
        depth_path = depth_dir / f"{direction}.png"
        normal_path = normal_dir / f"{direction}.png"
        image.save(albedo_path, "PNG")
        depth_out.save(depth_path, "PNG")
        normal_out.save(normal_path, "PNG")
        copied_albedo[direction] = albedo_path
        depth_paths[direction] = depth_path
        normal_paths[direction] = normal_path

    review_path = make_review_sheet(
        copied_albedo,
        depth_paths,
        normal_paths,
        directions=directions,
        out_path=map_root / "map_review.png",
        title=f"Nymphs Sprite maps: {subject}",
    )
    manifest = {
        "schema_version": "nymphs_sprite_maps_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "subject": subject,
        "source": source,
        "source_dir": str(subject_dir),
        "backend": backend,
        "model_id": resolved_model_id,
        "device": device,
        "sprite_size": sprite_size,
        "normal_strength": normal_strength,
        "detail_strength": detail_strength,
        "directions": list(copied_albedo.keys()),
        "outputs": {
            "root": str(map_root),
            "albedo": {k: str(v) for k, v in copied_albedo.items()},
            "depth": {k: str(v) for k, v in depth_paths.items()},
            "normal": {k: str(v) for k, v in normal_paths.items()},
            "review": str(review_path),
        },
        "notes": (
            "Depth is generated from the selected model backend, then normal is "
            "derived from that depth and all maps are resized to the final sprite "
            "grid. alpha_volume is fallback/debug only."
        ),
    }
    manifest_path = map_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return {
        "root": map_root,
        "manifest": manifest_path,
        "review": review_path,
        "count": len(copied_albedo),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Derive local Nymphs Sprite map candidates")
    parser.add_argument("--subject", required=True, help="Subject/output folder name")
    parser.add_argument("--input-dir", type=Path, help="Override subject output folder")
    parser.add_argument("--output-dir", type=Path, help="Override map output folder")
    parser.add_argument("--direction-count", type=int, default=8, choices=[8, 16])
    parser.add_argument("--source", choices=["cutout", "processed", "raw"], default="cutout")
    parser.add_argument("--backend", choices=["depth_anything", "midas", "alpha_volume"], default="depth_anything")
    parser.add_argument("--model-id", help="Override the default depth model for the selected backend")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--sprite-size", type=int, default=96)
    parser.add_argument("--normal-strength", type=float, default=3.0)
    parser.add_argument("--detail-strength", type=float, default=0.45, help="Only used by --backend alpha_volume")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = derive_maps(
        subject=args.subject,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        direction_count=args.direction_count,
        source=args.source,
        backend=args.backend,
        model_id=args.model_id,
        device=args.device,
        sprite_size=args.sprite_size,
        normal_strength=args.normal_strength,
        detail_strength=args.detail_strength,
    )
    print(f"Map stage complete: {result['count']} directions")
    print(f"Output: {result['root']}")
    print(f"Review: {result['review']}")
    print(f"Manifest: {result['manifest']}")


if __name__ == "__main__":
    main()
