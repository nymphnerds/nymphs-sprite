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
  generation, Sprite Foundry character presets, and a small candidate LoRA
  catalog.
- `models/` profiles: catalogs for Z-Image ControlNet Union and Depth Anything
  dependencies used by guided morphology and depth-map derivation.
- `ui/manager.html`: the NymphsCore Manager UI for the sprite flow.
- `ui/nymph_image_reference.html`: a copy of the existing Nymphs Image UI kept
  as a local reference while the sprite module owns its own controls.
- `docs/SPRITE_FOUNDRY_COMFYUI_PIPELINE.md`: the deep-dive notes for what
  those workflows do and what NymphsCore needs to replace.
- `docs/SPRITE_HANDOFF.md`: the current handoff and next-step tracker for the
  Nymphs Sprite / Sprite Foundry adaptation.
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

## Model Fetch

The Manager detail page exposes one native `Model Fetch` dropdown, matching the
other Nymphs modules. The default `Complete Sprite Stack` choice fetches all
first-run Sprite requirements:

```text
shared Z-Image INT4 r32 backend
tarn59 pixel-art LoRA
mks0813 pixel-art LoRA
Z-Image ControlNet Union
Depth Anything V2 Small
```

Shared backend model files delegate to Nymphs Image / Z-Image and use the same
cache and generation preset:

```text
$HOME/NymphsData/cache/huggingface
$HOME/NymphsData/config/zimage/generation-preset.env
```

Sprite-owned assets are still stored under the Sprite module paths below, so
either Nymphs Image or Nymphs Sprite can prepare the shared backend without
creating duplicate model caches.

## Pixel Art LoRA

The module includes a starter catalog in
`profiles/zimage_turbo_lora_candidates.json`.

The same `Model Fetch` dropdown also includes Sprite-only choices for repair or
testing. The complete asset package fetches both starter sprite LoRAs, plus the
staged ControlNet Union and Depth Anything assets without touching shared
Z-Image backend weights. The fetcher stores the selected LoRA preset at:

```text
$HOME/NymphsData/config/nymphs-sprite/selected_lora.env
```

`Generate 8-Way` reads that preset automatically unless you provide a custom
`--lora-path`.

Current default candidate:

```text
repo:     tarn59/pixel_art_style_lora_z_image_turbo
file:     pixel_art_style_z_image_turbo.safetensors
trigger:  Pixel art style.
base:     Tongyi-MAI/Z-Image-Turbo
```

Alternative candidate:

```text
repo:     mks0813/z-image-turbo-pixel-art-lora
file:     epoch-1.safetensors
trigger:  pxlstl
base:     Tongyi-MAI/Z-Image-Turbo
```

The mks0813 file is retained as an alternate asset, but the current Nunchaku
LoRA runtime rejects it with a tensor-shape mismatch during composition. The
tarn59 LoRA has passed a one-direction Sprite generation smoke test.

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
  --lora-path "$HOME/LoRA/loras/nymphs-sprite/mks0813--z-image-turbo-pixel-art-lora/epoch-1.safetensors" \
  --lora-trigger pxlstl
```

If `--lora-path` is omitted, the runner asks Nymphs Image `/api/loras` for the
latest available LoRA.

From the Manager UI, use **Open Z-Image** first. That starts the existing
Nymphs Image backend, then **Generate** calls `POST /generate` through the
module runner with the selected sprite LoRA settings.

Each generation batch also writes a Sprite Foundry-style artifact bundle under:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject-id>/<batch-id>
```

The bundle contains:

```text
directions/          copied per-direction image files when Z-Image returns local paths
sprite_batch.json    prompts, seeds, LoRA settings, source Z-Image responses, and paths
contact_sheet.png    quick visual sheet when Pillow is available
```

The sprite processor uses the MIT-licensed Sprite Foundry method as its
reference: background cleanup, foreground crop, square padding, nearest-neighbor
resize, alpha mechanical checks, and review sheets. The sprite size is a choice,
not hard-coded to Foundry's original 48px. `--sprite-size` accepts `24..512`
and defaults to `96` for Z-Image's more detailed pixel style. Useful test sizes:

```text
48   strict classic sprite
64   small but less brutal than 48
96   default; preserves more Z-Image detail
128  larger action-RPG / HD-2D sprite
192  chunky preview/game token scale
256  large portrait-token sprite
```

## Sprite Foundry Presets

The module keeps a generated catalog of the available Sprite Foundry character
configs at:

```text
profiles/foundry_character_presets.json
profiles/foundry_export_roster.json
```

The catalog is derived from the local `sprite-foundry/pipeline/chars` configs
and preserves full subject prompts, negative prompts, seeds, roles, body
classes, body locks, reject conditions, pack metadata, and source config paths.
The custom Manager UI uses this catalog for the prompt preset dropdown instead
of a small hand-written sample.

The original public Foundry roster describes 92 production export packs. This
module currently has direct generation presets for the Foundry character configs
available in the local fork. `foundry_export_roster.json` carries the 92-pack
lane/subject target; export-roster-only entries remain a parity target until
their prompt configs are available or reconstructed.

## Foundry Bridge

The custom UI has two generation lanes:

```text
Generate Sources / Generate + Process
  Fast module batch path under $HOME/NymphsData/outputs/nymphs-sprite.

Foundry Run
  Canonical Sprite Foundry fork path using foundry generate-nymphscore.
```

`Foundry Run` uses the selected imported preset's `source_config` path and calls
the local `sprite-foundry` fork. The default checkout is:

```text
$HOME/NymphsModules/sprite-foundry
```

Override it with:

```bash
export NYMPHS_SPRITE_FOUNDRY_ROOT=/path/to/sprite-foundry
```

Useful module actions:

```bash
bash $HOME/Nymphs-Sprite/scripts/nymphs_sprite_foundry_status.sh
bash $HOME/Nymphs-Sprite/scripts/nymphs_sprite_foundry_generate.sh \
  --source-config pipeline/chars/goblin_scout.json \
  --sprite-size 96
```

This path preserves Foundry's registry, gates, review queue, bakeoff artifacts,
and next-step commands. It still requires Nymphs Image / Z-Image to be running
at the configured `zimage_url`, plus a downloaded Z-Image Turbo pixel-art LoRA.

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

Status reports downloaded sprite LoRAs, ControlNet, and Depth Anything assets
back to the Manager. Sprite LoRA weights are deletable through the module-owned
`delete_models` entrypoint, one selected profile at a time.

The integration target is documented in
`profiles/zimage_turbo_controlnet_request.json`.
