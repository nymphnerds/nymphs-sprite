# Nymphs Sprite Handoff

Last updated: 2026-05-30

## North Star

Build `nymphs-sprite` as the NymphsCore module that adapts Sprite Foundry's
local sprite pipeline into a Nymphs-native workflow.

The target is not to run ComfyUI. The target is:

```text
Nymphs Sprite UI
  -> Nymphs Image / Z-Image Turbo / Nunchaku
  -> Z-Image Turbo pixel-art LoRA
  -> Foundry-style post-process
  -> transparent albedo sprites, sheets, gates, exports
  -> later: depth, normal, morphology/control parity
```

## Repo Map

```text
nymphnerds/nymphs-sprite
  NymphsCore module surface, Manager page, sprite LoRA fetch, sprite runner.
  Current reference commit in this workspace: dcd35ce.

nymphnerds/sprite-foundry
  Fork of mcp-tool-shop-org/sprite-foundry. Full upstream orchestration
  reference and adaptation lab.
  Current reference commit in this workspace: fb43975.

nymphnerds/zimage
  Nymphs Image runtime. Owns Z-Image Turbo, Nunchaku, LoRA loading, Qwen Image
  Edit, model fetch/delete, and Hugging Face cache path.
  Current pushed commit: fafa1e3, version 0.1.101.

nymphnerds/NymphsCore
  Manager shell and module-detail UX.
  Current pushed commit: e961bc6, Manager 0.9.72.

nymphnerds/nymphs-registry
  Public/dev registry.
  Current pushed commit: daedfda, registry_version 244.
```

## Current Decisions

- `nymphs-sprite` stays its own module and registry entry.
- Sprite Foundry is the reference system; useful orchestration should be ported
  or called intentionally, not re-invented casually.
- ComfyUI workflows are parity/reference material only.
- First generation path is Z-Image Turbo through Nymphs Image.
- Pixel art should use a Z-Image Turbo-compatible LoRA, not the original SDXL
  Pixel Art XL LoRA.
- Sprite output size is user-selectable, not fixed at 48px.
- Default sprite target is `96`; allowed range is `24..512`.
- Nymphs Sprite owns sprite-specific LoRAs/config/output. Nymphs Image owns
  base model and quantized weight fetching.

## Proven State

Nymphs Image / Z-Image:

- `zimage` is installed and running in the test WSL at `0.1.101`.
- Runtime status reports:

```text
models_ready=true
zimage_ready=true
weight_profile_selected=zimage_int4_r32
weight_profiles_downloaded=zimage_int4_r32
```

- The bad duplicate runtime cache path is fixed. Runtime/fetch status now use:

```text
$HOME/NymphsData/cache/huggingface
```

not:

```text
$HOME/.cache/huggingface/hub
```

- A fresh model load completed successfully after the fix. The log showed
  pipeline components and checkpoint shards loading, then:

```text
POST /api/model/load HTTP/1.1" 200 OK
```

- The latest slow-looking load did not show a new duplicate default-cache fetch.
  It was model/pipeline initialization with coarse UI progress around `8%`.

Manager / model cache UX:

- Manager `0.9.72` renders downloaded weight profiles in the `// MODEL CACHE`
  detail area as clickable items.
- Clicking a cached weight asks for confirmation, then calls the module-owned
  delete action:

```bash
scripts/zimage_delete_models.sh --profile <profile> --yes
```

- `zimage_delete_models.sh` validates profile ids against an allow-list and
  deletes only the selected cached weight/blob.
- The module guide documents this contract.
- Right-rail `Delete Data` remains separate and must not delete shared model
  caches.

Nymphs Sprite module:

- Installs as:

```text
$HOME/Nymphs-Sprite
```

- Manager UI lives at:

```text
ui/manager.html
```

- Selected LoRA config is stored at:

```text
$HOME/NymphsData/config/nymphs-sprite/selected_lora.env
```

- Generated batches write under:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject-id>/<batch-id>
```

- Current batch artifacts:

```text
directions/
contact_sheet.png
sprite_batch.json
```

- Foundry-style Python post-process exists:
  background cleanup, foreground crop, square pad, nearest-neighbor sprite
  resize, transparent albedo output, preview/contact sheets, and mechanical
  checks.

Sprite Foundry fork:

- `foundry generate-nymphscore` exists.
- It calls Nymphs Image instead of ComfyUI for generation.
- It registers per-direction seeds.
- `foundry_maps.py` follows run `sprite_target` instead of hard-coded `48`.
- `verify.sh` passes with Python 3 fallback.

## Model And Fetch Boundaries

Nymphs Image owns:

```text
Tongyi-MAI/Z-Image-Turbo
nunchaku-ai/nunchaku-z-image-turbo
Qwen/Qwen-Image-Edit-2511
QuantFunc/Nunchaku-Qwen-Image-EDIT-2511
```

Nymphs Image fetch choices:

```text
Complete INT4 package
  Z-Image Turbo base + INT4 Z-Image weights + INT4 Qwen Edit weights

Complete FP4 package
  Z-Image Turbo base + FP4 Z-Image weights + FP4 Qwen Edit weights

Individual choices
  available for partial install, testing, and repair
```

These are hardware/runtime choices, not sprite modes.

Nymphs Sprite owns:

```text
Z-Image Turbo pixel-art LoRAs
sprite-specific generation defaults
sprite post-process config
future morphology/depth/control references
```

LoRA paths:

```text
$HOME/LoRA/loras
$HOME/LoRA/loras/nymphs-sprite
```

## Sprite Output Policy

Keep these rules:

- Generate from Z-Image at a practical source size for quality.
- Preserve raw generated images.
- Post-process down to `sprite_target` with nearest-neighbor resizing.
- Never hard-code `48`.
- Store selected target size in batch metadata.
- Use `96` as the first-test default.
- Keep broad output range available: `24..512`.

Expected per-direction outputs:

```text
raw source image
cleaned transparent albedo
preview/composited image
future depth map
future normal map
```

## Python Post-Process Contract

Keep post-process as ordinary Python so it can run without ComfyUI.

Current responsibilities:

- load generated direction image
- identify/remove simple background when possible
- build alpha mask
- crop to foreground bounds
- square-pad around the subject
- resize to `sprite_target` with nearest-neighbor sampling
- write transparent PNG albedo
- write preview PNG
- write contact sheet
- write `sprite_batch.json`
- run mechanical checks for file count, dimensions, transparency, non-empty
  foreground, prompt/seed/LoRA/size/source metadata

Next post-process improvements:

- stronger background cleanup options
- configurable padding
- per-direction crop consistency checks
- palette assist / color-count reporting
- optional indexed-color export
- depth/normal artifact registration
- export-pack writer compatible with Sprite Foundry expectations

## Control, Depth, And Morphology Plan

Do not make ComfyUI a runtime dependency. Use Sprite Foundry's ComfyUI workflow
as a parity map.

Sprite Foundry uses ComfyUI for:

```text
generation
LoRA application
ControlNet/morphology guidance
depth preprocessing
normal/depth map generation path
history/artifact retrieval
```

Nymphs replacement order:

1. Z-Image generation.
   - Use Nymphs Image API.
   - Use Z-Image Turbo/Nunchaku.
   - Use selected Z-Image Turbo pixel-art LoRA.
   - Preserve raw outputs.

2. Sprite post-process.
   - Cleanup, crop, resize, alpha, gates, contact sheet.
   - Confirm quality before adding heavier control paths.

3. Depth extraction.
   - Check what Depth Anything/depth tooling is already available in
     NymphsCore/Nymphs Image.
   - Store depth per direction.
   - Keep optional at first.

4. Normal maps.
   - Derive from depth unless a better native model path exists.
   - Validate with a simple lighting preview.

5. Morphology/control.
   - Audit whether current Z-Image/Nunchaku exposes real ControlNet-like image
     conditioning.
   - If yes, expose reference controls.
   - If no, use a two-pass strategy: generate albedo first, derive/refine maps
     later with post-process/Qwen-edit style tools.

6. Export parity.
   - Match Foundry pack layout.
   - Include albedo, depth, normal, manifest, checksums, subject metadata, run
     provenance.

## Foundry Parity Checklist

Keep these ideas:

- subject registry
- deterministic run/attempt records
- per-direction prompts and seeds
- raw artifact preservation
- mechanical gates
- review sheets/contact sheets
- accepted/rejected attempt lifecycle
- depth/normal map derivation
- deterministic export packs

Replace these assumptions:

- SDXL/Juggernaut checkpoint
- SDXL Pixel Art XL LoRA
- ComfyUI prompt/history API
- ComfyUI ControlNet nodes
- ComfyUI MiDaS/DepthAnything preprocessors

## Immediate Next Work

1. Install/update `nymphs-sprite` from the dev registry in the test WSL.
   - Confirm module appears only in dev mode.
   - Confirm detail page layout matches other modules.
   - Confirm LoRA fetch works.

2. Pick and fetch the first Z-Image Turbo pixel-art LoRA.
   - Store it under the sprite LoRA path.
   - Confirm selected LoRA config is written.
   - Confirm Nymphs Image can load/generate with it.

3. Run the first small sprite batch.
   - Backend: Z-Image Turbo INT4 r32.
   - Target size: `96`.
   - Subject: simple creature/gnome test.
   - Output: one eight-direction batch.
   - Inspect raw outputs, transparent albedo files, and contact sheet.

4. Compare against Sprite Foundry.
   - Check crop behavior.
   - Check background removal.
   - Check alpha gates.
   - Check direction consistency.
   - Check sheet layout.

5. Decide integration split after the first real batch.
   - Keep `nymphs-sprite` as the user-facing module.
   - Keep `sprite-foundry` as deeper orchestration/export reference.
   - Either call Foundry from the module or port exact pieces once the module
     path is proven.

## Do Not Forget

- Preserve upstream Sprite Foundry attribution and MIT notices.
- Do not put Sprite Foundry code into `nymphs-sprite` without updating third
  party notices.
- Do not make ComfyUI a dependency of Nymphs Sprite.
- Do not assume model paths. Verify cache path, env, status, and runtime load.
- Keep destructive cleanup module-owned.
- Keep the module simple enough to test from a clean WSL.
