# Nymphs Sprite

Nymphs Sprite is a NymphsCore module scaffold for adapting
`mcp-tool-shop-org/sprite-foundry` into a native Nymphs sprite pipeline.

The active target is Z-Image Turbo with a Z-Image-compatible sprite LoRA through
the Nymphs Image backend. The upstream ComfyUI graphs are kept as reference
material so we can match the behavior without adopting its SDXL/Juggernaut
runtime.

## What Is Here

- `comfyui_workflows/`: API-format ComfyUI workflow templates extracted from
  the upstream Sprite Foundry pipeline for parity notes only.
- `profiles/`: Nymphs-native request templates for Z-Image Turbo sprite
  generation and a small candidate LoRA catalog.
- `models/` profiles: catalogs for Z-Image ControlNet Union and Depth Anything
  dependencies used by guided morphology and depth-map derivation.
- `ui/manager.html`: the NymphsCore Manager UI for the sprite flow.
- `ui/nymph_image_reference.html`: a copy of the existing Nymphs Image UI kept
  as a local reference while the sprite module owns its own controls.
- `docs/SPRITE_FOUNDRY_COMFYUI_PIPELINE.md`: the deep-dive notes for what
  those workflows do and what NymphsCore needs to replace.
- `scripts/`: standard Nymphs module lifecycle scripts.
- `nymph.json`: module manifest for NymphsCore Manager.

## Upstream Split

Sprite Foundry has two useful halves:

```text
Foundry orchestration: subjects, attempts, gates, reviews, export contract
Execution layer: ComfyUI SDXL generation, ControlNet morphology, normal/depth maps
```

The work for NymphsCore is to keep the orchestration ideas, then replace the
ComfyUI execution layer with Nymphs-owned module stages. For generation, that
means targeting:

```text
provider:  zimage
model:     Tongyi-MAI/Z-Image-Turbo
LoRA:      a Z-Image Turbo-compatible sprite/pixel LoRA
endpoint:  Nymphs Image POST /generate
```

For guided morphology, the first target is:

```text
controlnet: alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union
modes:      canny, hed, depth, pose, mlsd
status:     staged by Nymphs Sprite; requires a Z-Image ControlNet backend path
```

For depth maps and depth conditioning refs, the first target is:

```text
depth: depth-anything/Depth-Anything-V2-Small-hf
```

## Current Status

This module now installs a Manager-hosted sprite UI and a Nymphs-native
direction runner. The first working flow is:

```text
Nymphs Sprite UI -> Open Z-Image -> fetch/select Z-Image Turbo LoRA -> Generate 8-Way
```

The copied Nymphs Image UI is kept in `ui/nymph_image_reference.html` for parity
work, but `ui/manager.html` is the module-owned screen. It calls Manager module
actions instead of direct browser fetches, so it can run as `local_html`.

## Install Paths

Default install root:

```text
$HOME/Nymphs-Sprite
```

Default data roots:

```text
$HOME/NymphsData/outputs/nymphs-sprite
$HOME/NymphsData/config/nymphs-sprite
$HOME/NymphsData/logs/nymphs-sprite
```

Default LoRA library root:

```text
$HOME/LoRA/loras
```

## Pixel Art LoRA

The module includes a starter catalog in
`profiles/zimage_turbo_lora_candidates.json`.

The Manager detail page exposes this through a native `LoRA Fetch` action group,
matching the compact Fetch Models layout used by Nymphs Image, TRELLIS, and
Pixal3D. Pick a LoRA from the dropdown and press Fetch LoRA. The fetcher stores
the selected preset at:

```text
$HOME/NymphsData/config/nymphs-sprite/selected_lora.env
```

`Generate 8-Way` reads that preset automatically unless you provide a custom
`--lora-path`.

Current default candidate:

```text
repo:     mks0813/z-image-turbo-pixel-art-lora
file:     z-image-turbo-pixel-art-lora.safetensors
trigger:  pxlstl
base:     Tongyi-MAI/Z-Image-Turbo
```

Alternative candidate:

```text
repo:     tarn59/pixel_art_style_lora_z_image_turbo
trigger:  Pixel art style.
base:     Tongyi-MAI/Z-Image-Turbo
```

After install, the fetch script can place a selected LoRA under:

```text
$HOME/LoRA/loras/nymphs-sprite
```

Your Nymphs Image source already owns LoRA loading:

- `ZIMAGE_LORA_ROOT` defaults to `$HOME/LoRA/loras`.
- `GET /api/loras` lists available `.safetensors` files and run folders.
- `POST /generate` accepts `lora_path` and `lora_scale`.
- the Z-Image model manager applies the LoRA to the loaded Z-Image pipeline.

Nymphs Sprite uses that path directly. The direction runner is:

```bash
scripts/nymphs_sprite_generate_directions.sh \
  --subject-id hero_test \
  --subject-prompt "armored forest knight with a short cloak" \
  --lora-path "$HOME/LoRA/loras/nymphs-sprite/mks0813--z-image-turbo-pixel-art-lora/z-image-turbo-pixel-art-lora.safetensors" \
  --lora-trigger pxlstl
```

If `--lora-path` is omitted, the runner asks Nymphs Image `/api/loras` for the
latest available LoRA.

From the Manager UI, use **Open Z-Image** first. That starts the existing
Nymphs Image backend, then **Generate** calls `POST /generate` through the
module runner with the selected sprite LoRA settings.

## ControlNet And Depth

The current local Z-Image runtime has:

```text
ZImagePipeline
ZImageImg2ImgPipeline
NunchakuZImageTransformer2DModel with LoRA methods
```

It does not currently expose:

```text
ZImageControlNetPipeline
ZImage ControlNet model class
```

Nymphs Sprite still stages the models now so the next backend work has no hidden
download step:

```bash
scripts/nymphs_sprite_fetch_controlnet.sh
scripts/nymphs_sprite_fetch_depth_anything.sh
scripts/nymphs_sprite_check_runtime.sh
```

The integration target is documented in
`profiles/zimage_turbo_controlnet_request.json`.
