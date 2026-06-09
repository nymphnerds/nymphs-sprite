"""
Pixelation / downscale utility for the foundry normalization pipeline.

Takes a higher-res generated sprite and produces a clean 48x48 pixel art result
using nearest-neighbor downscale (preserves crisp pixel edges).

Usage:
    python pipeline/pixelate.py <input_path> <output_path> [--size 48]
    python pipeline/pixelate.py <input_path> <output_path> --size 48 --palette 16

As a library:
    from pipeline.pixelate import pixelate_sprite
    pixelate_sprite("big.png", "small.png", target_size=48)
"""

import argparse
import sys
from pathlib import Path
from PIL import Image


def pixelate_sprite(
    input_path: str,
    output_path: str,
    target_size: int = 48,
    palette_colors: int | None = None,
) -> Path:
    """Downscale a generated sprite to target pixel size with crisp edges.

    Args:
        input_path: Source image (any size, must have alpha channel for sprites).
        output_path: Destination PNG path.
        target_size: Final pixel dimension (square). Default 48.
        palette_colors: Optional color count limit for palette reduction.

    Returns:
        Path to the saved output file.
    """
    img = Image.open(input_path)

    # Preserve alpha if present
    if img.mode == "RGBA":
        # Nearest-neighbor resize preserves hard pixel edges
        result = img.resize((target_size, target_size), Image.NEAREST)
    elif img.mode == "RGB":
        result = img.resize((target_size, target_size), Image.NEAREST)
    elif img.mode == "L":
        # Grayscale (depth maps, masks)
        result = img.resize((target_size, target_size), Image.NEAREST)
    else:
        # Convert to RGBA and resize
        result = img.convert("RGBA").resize((target_size, target_size), Image.NEAREST)

    # Optional palette reduction
    if palette_colors is not None and palette_colors > 0:
        if result.mode == "RGBA":
            # Separate alpha, quantize RGB, reattach
            alpha = result.split()[3]
            rgb = result.convert("RGB")
            quantized = rgb.quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT)
            rgb_result = quantized.convert("RGB")
            result = rgb_result.convert("RGBA")
            result.putalpha(alpha)
        else:
            quantized = result.quantize(colors=palette_colors, method=Image.Quantize.MEDIANCUT)
            result = quantized.convert(img.mode)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.save(str(out), "PNG")
    return out


def main():
    parser = argparse.ArgumentParser(description="Pixelate/downscale sprites to target size")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", help="Output PNG path")
    parser.add_argument("--size", type=int, default=48, help="Target pixel size (default: 48)")
    parser.add_argument("--palette", type=int, default=None, help="Optional palette color limit")
    args = parser.parse_args()

    result = pixelate_sprite(args.input, args.output, args.size, args.palette)
    print(f"Pixelated: {args.input} -> {result} ({args.size}x{args.size})")


if __name__ == "__main__":
    main()
