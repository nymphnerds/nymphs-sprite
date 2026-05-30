# Nymphs Sprite Handoff

Last updated: 2026-05-30

## Goal

Build `nymphs-sprite` as the NymphsCore module that turns Sprite Foundry's
local sprite pipeline into a Nymphs-native workflow.

The target is not to run ComfyUI. The target is:

```text
Nymphs Sprite UI
  -> Nymphs Image / Z-Image Turbo / Nunchaku
  -> Z-Image Turbo pixel-art LoRA
  -> Foundry-style cleanup, crop, sprite resize, gates, sheets
  -> later: depth, normal, morphology control, export parity
```

## Repositories

```text
nymphnerds/nymphs-sprite
  NymphsCore module surface, Manager page, fetch actions, sprite runner.

nymphnerds/sprite-foundry
  Fork of mcp-tool-shop-org/sprite-foundry. Keep as the full upstream
  orchestration reference and adaptation lab.

nymphnerds/zimage
  Nymphs Image runtime. Owns Z-Image Turbo, Nunchaku, LoRA loading, Qwen Image
  Edit, and the shared Hugging Face cache path.
```

## Current Decisions

- `nymphs-sprite` is its own module directory and registry entry.
- Sprite Foundry is the reference system; do not re-invent its useful
  orchestration ideas casually.
- ComfyUI workflows are kept only as parity/reference material.
- Generation starts with Z-Image Turbo through Nymphs Image.
- Pixel art comes from a Z-Image Turbo-compatible LoRA, not the original SDXL
  Pixel Art XL LoRA.
- Sprite output size is configurable, not fixed at 48px.
- Default sprite size is `96`; allowed range is `24..512`.
- Keep individual LoRA/model choices visible, but offer sane package choices
  where fetching is involved.

## What Works Now

In `nymphs-sprite`:

- Module installs as `$HOME/Nymphs-Sprite`.
- Manager UI lives at `ui/manager.html`.
- LoRA fetch action stores selected LoRA config at:

```text
$HOME/NymphsData/config/nymphs-sprite/selected_lora.env
```

- Generated batches write to:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject-id>/<batch-id>
```

- Current batch artifacts:

```text
directions/
contact_sheet.png
sprite_batch.json
```

- Foundry-style post-process is implemented:
  background cleanup, foreground crop, square pad, nearest-neighbor resize,
  transparent albedo output, preview/contact sheets, and mechanical checks.
- Pixel resolution choices are exposed in the UI.
  - Default: `96`.
  - Allowed: `24..512`.
  - The intent is artist choice, not a single fixed 48px pipeline.

In `sprite-foundry` fork:

- `foundry generate-nymphscore` exists.
- It calls Nymphs Image instead of ComfyUI for generation.
- It registers per-direction seeds correctly.
- `foundry_maps.py` follows `sprite_target` instead of hard-coded `48`.
- `verify.sh` passes with Python 3 fallback.

In `zimage`:

- LoRA loading is wired for Z-Image Turbo/Nunchaku.
- Model cache pathing was fixed so runtime load uses:

```text
/home/nymph/NymphsData/cache/huggingface
```

instead of falling back to:

```text
/home/nymph/.cache/huggingface/hub
```

## Pixel Resolution Policy

Sprite Foundry's original project centers around small finished sprites. For
Nymphs Sprite, output size must be selectable because the source model/LoRA may
produce better detail above 48px.

Keep these rules:

- Generate from Z-Image at a practical image size for quality.
- Post-process down to the requested sprite target with nearest-neighbor
  resizing.
- Preserve raw generated images beside processed sprite outputs.
- Do not hard-code `48`.
- Store the chosen target size in batch metadata.
- Use `96` as the default first-test target.
- Keep a broad range available, currently `24..512`.

Expected output layers per direction:

```text
raw source image
cleaned transparent albedo
preview/composited image
future depth map
future normal map
```

## Python Post-Process Plan

The post-process should stay as ordinary Python inside the module/foundry path
so it can be tested without ComfyUI.

Current responsibilities:

- load generated direction image
- identify and remove flat/simple background when possible
- build alpha mask
- crop to foreground bounds
- square-pad around the subject
- resize to `sprite_target` with nearest-neighbor sampling
- write transparent PNG albedo
- write preview PNG
- write contact sheet
- write `sprite_batch.json`
- run mechanical checks:
  - expected file count
  - dimensions match selected sprite target
  - transparency exists
  - foreground is not empty
  - metadata records prompt, seed, LoRA, size, and source paths

Next Python additions:

- stronger alpha/background cleanup options
- configurable padding
- per-direction crop consistency checks
- palette assist / color-count reporting
- optional indexed-color export
- normal/depth artifact registration once those maps exist
- export-pack writer compatible with Sprite Foundry's pack expectations

Keep the Python path deterministic: same prompt, seed, LoRA, target size, and
source image should produce the same processed outputs.

## ControlNet, Depth, And Morphology Plan

Do not treat ComfyUI ControlNet nodes as required runtime dependencies. Treat
them as a map of what Sprite Foundry uses and replace them with Nymphs-native
steps.

Sprite Foundry uses the ComfyUI side for:

```text
generation
LoRA application
ControlNet/morphology guidance
depth preprocessing
normal/depth map generation path
history/artifact retrieval
```

Nymphs Sprite replacement plan:

1. Z-Image generation first.
   - Use Nymphs Image API.
   - Use Z-Image Turbo/Nunchaku.
   - Use selected Z-Image Turbo pixel-art LoRA.
   - Keep raw outputs.

2. Sprite post-process second.
   - Use the Python cleanup/crop/resize/gate path above.
   - Produce transparent albedo and contact sheet before adding heavier control
     features.

3. Depth extraction next.
   - Add a sprite module asset/runtime path for Depth Anything or equivalent
     only after checking what is already available in Nymphs Image/NymphsCore.
   - Store depth maps per direction.
   - Keep depth output optional at first.

4. Normal map derivation after depth.
   - Derive normals from depth if no better native model path exists.
   - Match Sprite Foundry export naming expectations.
   - Validate in a simple lighting preview before calling it done.

5. Morphology/control guidance after the backend is real.
   - Audit whether the current Z-Image/Nunchaku path supports ControlNet-like
     conditioning.
   - If yes, expose Nymphs Sprite controls for morphology reference images.
   - If no, use a two-pass plan: generate albedo first, derive/refine maps with
     post-process/Qwen edit style tools later.

6. Export parity last.
   - Match Foundry pack layout.
   - Include albedo, depth, normal, manifest, checksums, subject metadata, and
     run provenance.

Open questions to verify before implementation:

- Which depth model is already available or acceptable inside NymphsCore?
- Does the Nunchaku Z-Image runtime expose any control/image-conditioning path?
- Should morphology references live in `nymphs-sprite` assets or in a shared
  NymphsData library?
- Which export layout does the first game/tool consumer need?

## Fetching And Model Path Rules

Nymphs Sprite should not own Z-Image base model fetching. That belongs to
Nymphs Image.

Nymphs Sprite owns sprite-specific assets:

```text
Z-Image Turbo pixel-art LoRAs
future morphology/depth/control references
future sprite-specific post-process config
```

Nymphs Image owns:

```text
Tongyi-MAI/Z-Image-Turbo
nunchaku-ai/nunchaku-z-image-turbo
Qwen/Qwen-Image-Edit-2511
QuantFunc/Nunchaku-Qwen-Image-EDIT-2511
```

Nymphs Image model fetch should keep hardware-level package choices:

```text
Complete INT4 package
  Z-Image Turbo base + INT4 Z-Image weights + INT4 Qwen Edit weights

Complete FP4 package
  Z-Image Turbo base + FP4 Z-Image weights + FP4 Qwen Edit weights

Individual choices
  still available for manual installs, testing, and partial repair
```

These are not separate sprite modes. They are runtime package choices depending
on GPU/VRAM and should align with Blender addon expectations.

All Hugging Face model paths should resolve through:

```text
$HOME/NymphsData/cache/huggingface
```

LoRA library path:

```text
$HOME/LoRA/loras
$HOME/LoRA/loras/nymphs-sprite
```

## Foundry Parity Checklist

Keep these Sprite Foundry ideas:

- subject registry
- deterministic run/attempt records
- per-direction prompts and seeds
- raw artifact preservation
- mechanical gates
- review sheets/contact sheets
- accepted/rejected attempt lifecycle
- depth/normal map derivation
- deterministic export packs

Replace these execution assumptions:

- SDXL/Juggernaut checkpoint
- SDXL Pixel Art XL LoRA
- ComfyUI prompt/history API
- ComfyUI ControlNet nodes
- ComfyUI MiDaS/DepthAnything preprocessors

## Next Work

1. Test the updated `zimage` cache-path fix in the test WSL.
   - Delete the duplicate default HF cache if needed.
   - Re-fetch/load and confirm it does not recreate
     `/home/nymph/.cache/huggingface/hub/models--nunchaku-ai--nunchaku-z-image-turbo`.

2. Install/update `nymphs-sprite` from registry in test WSL.
   - Confirm the module appears only in dev mode.
   - Confirm Manager detail page layout matches other modules.
   - Confirm LoRA fetch works.

3. Run a small sprite batch.
   - Use Z-Image Turbo INT4 r32 first.
   - Use a Z-Image Turbo pixel-art LoRA.
   - Generate one eight-direction batch at `96`.
   - Inspect contact sheet and transparent albedo outputs.

4. Compare against Sprite Foundry.
   - Run or inspect equivalent Foundry post-process expectations.
   - Note mismatches in crop, background removal, alpha gates, and sheet layout.

5. Decide the integration split.
   - Keep `nymphs-sprite` as the user-facing module.
   - Keep `sprite-foundry` fork as the deeper orchestration/export engine.
   - Either call into Foundry from the module later, or port the exact pieces
     needed once the module path is proven.

6. Add depth/morphology in order.
   - Depth Anything path first.
   - Normal-map derivation second.
   - Z-Image ControlNet/morphology only after the Z-Image backend exposes a real
     ControlNet-capable path.

## Do Not Forget

- The upstream author did the hard orchestration work; preserve attribution.
- Do not put Sprite Foundry code into `nymphs-sprite` without keeping MIT
  notices current.
- Do not make ComfyUI a dependency of Nymphs Sprite.
- Do not assume model paths. Verify cache path, env, status, and runtime load.
- Keep the module simple enough to test from a clean WSL.
