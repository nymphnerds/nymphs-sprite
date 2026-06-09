# Nymphs Sprite Distillation Plan

Current as of 2026-06-09.

This is the single current handoff for Nymphs Sprite. The old Sprite Foundry
docs remain useful reference material, but this doc is the clean resume point
for the new module.

## North Star

Nymphs Sprite should be a slick, reliable sprite-set generator for games.

The old Sprite Foundry project had good ideas, but it exposed too many
experimental paths at once. Nymphs Sprite should distill the strongest parts
into a dependable workflow:

```text
Character -> Guide -> Style -> Generate -> Review -> Export
```

The product should feel like directing a sprite sheet, not configuring an AI
pipeline.

## Repo And Environment

Active product repo:

```text
/home/nymph/NymphsModules/nymphs-sprite
https://github.com/nymphnerds/nymphs-sprite
```

Reference-only source:

```text
/home/nymph/NymphsModules/sprite-foundry
https://github.com/nymphnerds/sprite-foundry
```

Important: keep the local `sprite-foundry` checkout on the dev WSL. It is the
reference module. Do not delete it from dev. It should not appear in the test
Manager registry anymore, but it can stay locally for comparison.

Test WSL:

```text
\\wsl.localhost\NymphsCore
wsl.exe -d NymphsCore --cd /home/nymph -- ...
```

The test WSL is where Manager install/update/runtime validation happens. Use
Manager installs and registry updates for real validation unless there is a
clear reason to inspect files directly.

## Current Published State

Current published module version:

```text
Nymphs Sprite 1.2.12
```

Current module identity:

```text
id: nymphs-sprite
name: Nymphs Sprite
short_name: NS
category: image
kind: sprite
runtime port: 8098
ui: http://127.0.0.1:8098/nymph
```

Default paths:

```text
$HOME/Nymphs-Sprite
$HOME/NymphsData/outputs/nymphs-sprite
$HOME/NymphsData/config/nymphs-sprite
$HOME/NymphsData/logs/nymphs-sprite
$HOME/NymphsData/tmp/nymphs-sprite
$HOME/NymphsData/cache/huggingface
$HOME/LoRA/loras
```

Registry:

```text
/home/nymph/NymphsModules/nymphs-registry/nymphs-dev.json
```

The dev registry should point at the Nymphs Sprite manifest, not Sprite Foundry.

## Output Ownership Rule

Nymphs Image / Z-Image is the backend engine only. Nymphs Sprite owns the
workflow and should own the generated artifacts.

Final sprites, guide sheets, review artifacts, accepted sets, exports, and
Nymphs Sprite logs should stay under Nymphs Sprite-owned folders:

```text
$HOME/NymphsData/outputs/nymphs-sprite/
$HOME/NymphsData/tmp/nymphs-sprite/
$HOME/NymphsData/config/nymphs-sprite/
$HOME/NymphsData/logs/nymphs-sprite/
```

Do not silently dump final sprite assets into generic Nymphs Image / Z-Image
output folders. Passing an explicit output directory to the backend is the
correct pattern.

## Current Runtime Model

The intended generation stack is:

```text
Nymphs Sprite UI
  -> local Nymphs Sprite module server
  -> Nymphs Image / Z-Image backend API
  -> Z-Image Turbo / Nunchaku
  -> optional Z-Image pixel-art LoRA
  -> Nymphs Sprite output folder
```

The `Start` button starts the Nymphs Image / Z-Image backend when needed. It is
not a separate sprite-specific model runtime.

The custom UI status panel should now read the local `/api/status` endpoint
first, then fall back to the Manager bridge only if local status fails. This was
changed in `1.2.12` because the previous bridge-first path made the UI look
broken when a stale DOM reference threw during render.

## Current Model And LoRA Handling

Profile names are Nymphs Sprite names only:

```text
nymphs_sprite_starter_stack
nymphs_sprite_controlnet_2_1
nymphs_sprite_all_loras
nymphs_sprite_lora_mks0813_pixel_art
nymphs_sprite_lora_skyasl_pixel_artist
nymphs_sprite_lora_tarn59_pixel_art
```

Do not keep old `sprite_foundry_*` profile aliases in the user-facing manifest,
fetch selector, or delete selector.

The current status script can detect these bundled LoRA choices from the shared
LoRA folder:

```text
$HOME/LoRA/loras/mks0813_pixel_art/mks0813_pixel_art.safetensors
$HOME/LoRA/loras/skyasl_pixel_artist/skyasl_pixel_artist.safetensors
$HOME/LoRA/loras/tarn59_pixel_art/tarn59_pixel_art.safetensors
```

It also scans `$HOME/LoRA/loras` for additional `.safetensors` files and should
list usable local LoRAs in the UI dropdown. Bundled LoRAs get known triggers:

```text
mks0813: pxlstl
SkyAsl: a pixel art character
tarn59: Pixel art style.
```

If the UI says "Could not read module status" or the LoRA dropdown is empty,
first test these in the test WSL:

```bash
/home/nymph/Nymphs-Sprite/scripts/sprite_foundry_status.sh | sed -n '1,80p'
curl -sS --max-time 4 http://127.0.0.1:8098/api/status | sed -n '1,80p'
```

The status output should include `lora_choices=...`, `selected_lora_path=...`,
and `zimage_running=...`.

## What We Kept From Sprite Foundry

Keep these ideas:

- 8-direction sprite-set target.
- Per-direction review, accept, reject, and regenerate.
- Audition loops instead of throwing away the whole set.
- Contact sheets and preview strips.
- Deterministic output folders and export manifests.
- Prompt presets as repeatable test fixtures.
- Godot packaging interest.
- Normal/depth map ambitions for game lighting.
- Lifecycle metadata where it helps debugging and reproducibility.

Hide or demote these:

- Too many generation methods on the main screen.
- Run IDs and attempt IDs in the normal path.
- Foundry internals as first-screen controls.
- ComfyUI-first assumptions.
- Backend details as the product concept.

Inherited advanced buttons can remain under an Advanced section while the new
flow is being proven, but they should not define the everyday workflow.

## Generation Methods Clarified

### NymphsCore / Z-Image

This is the main path for Nymphs Sprite.

Today this path uses Z-Image / Nunchaku / LoRA for generation. The copied code
does not yet fully pass per-direction ControlNet guide images into Z-Image.
That wiring is the next real milestone after basic install/status/generation
testing is stable.

### Stack A v2

Original ComfyUI/JuggernautXL plus pixel-art LoRA path. Useful as historical
reference and comparison material, but not the core Nymphs Sprite runtime.

### Morph ControlNet

Original ComfyUI path using body-class depth/canny style control. The concept is
important: body classes and guides can stabilize silhouette and direction. The
implementation is legacy.

### Turnaround Sheet

Original CharTurn-style multi-view sheet idea. Useful for identity research and
maybe future audition/regen, but not the first clean path. We decided not to
block on finding a Z-Image CharTurn LoRA. Use ControlNet refs instead.

## ControlNet Mental Model

ControlNet does not create the body guide. Nymphs Sprite creates or receives the
guide first. Z-Image then uses that guide as visual conditioning.

```text
prompt says what the sprite is
LoRA says the visual style
guide image says where the body/pose/outline should be
Z-Image generates the sprite from those inputs
```

Relevant ControlNet modes for Z-Image Turbo ControlNet Union 2.1:

- Pose: best for stick-rig/body joint control.
- Scribble: best for hand-drawn sketch silhouettes.
- Canny/HED: best for outlines from a sketch or existing sprite.
- Depth: useful later for volume/lighting/isometric experiments.
- MLSD: hard-surface lines; not a main character path.
- Gray: research-only until tested.

User-facing language should be:

- Direction Guides
- Pose Guide
- Sketch Guide
- Outline Guide
- Body Guide

Avoid leading with technical words like preprocessor, control map, union model,
or ControlNet scale except in Advanced.

## The Pose / Guide Panel

This is the strongest future idea.

The Guide panel should let the user create or adjust the exact ControlNet refs
used for generation. The simple version comes first:

1. Choose body type.
2. Generate an 8-direction guide sheet.
3. Preview the guide sheet.
4. Generate the sprite set using those guides.

Body types:

- humanoid
- wide squat
- tall thin
- amorphous
- quadruped
- winged
- custom

Later, the panel can support:

- stick-figure pose editing
- rough sketch drawing
- per-direction manual adjustment
- copy/mirror pose between directions
- weapon/prop guide lines
- deriving a guide from an auditioned/generated image
- regenerating one bad direction with a corrected guide

Future advanced loop:

```text
bad direction -> make/edit guide -> regenerate that direction -> accept winner
```

## Best Working Flow To Build First

Build and test from the top down.

### 1. Character

- Pick a preset or write a prompt.
- Set subject ID.
- Keep prompt and negative prompt visible.
- Prompt presets are test fixtures, not the whole product.

### 2. Guide

- Pick body type.
- Generate deterministic 8-direction guide refs.
- Show a guide contact sheet.
- Save guide files under Nymphs Sprite outputs/tmp.

### 3. Style

- Pick LoRA.
- Pick sprite size and palette options.
- Keep advanced model/rank/seed/step controls available but not dominant.

### 4. Generate

- Generate all 8 directions through Z-Image.
- Use body/direction guides as ControlNet refs once wired.
- Save into Nymphs Sprite output folders.
- One main button should cover the normal path.

8 directions:

```text
front
front_left
left
back_left
back
back_right
right
front_right
```

16-direction support is desired later, after 8-direction quality is dependable.

### 5. Review

- Use a preview strip/audition UX inspired by Nymphs Image.
- Select winners.
- Reject weak directions.
- Regenerate selected directions without losing accepted ones.

### 6. Export

- Export a clean game-ready pack.
- Preserve interest in Godot packaging.
- Keep normal/depth maps as a future export layer.

## Audition / Regenerate Stage

The audition stage should stay simple:

- generate candidates
- inspect in preview strip
- select winner per direction
- regenerate only failed directions
- export accepted set

This stage is where the pose panel becomes powerful later. A bad generated
direction can become the starting point for a manual pose, sketch, or outline
ref.

## Godot / Packaging

Godot export remains a real goal, but should not block the first reliable
generator.

Target export contents:

- accepted direction PNGs
- contact sheet
- manifest JSON
- optional normal maps
- optional depth maps
- Godot-ready import folder/package
- checksums/provenance for reproducibility

Likely direction filenames:

```text
front.png
front_left.png
left.png
back_left.png
back.png
back_right.png
right.png
front_right.png
contact_sheet.png
manifest.json
```

## Normal / Depth Post-Process

The original project had depth/normal-map ambitions and export folders for
albedo, depth, and normal. Keep this as a second-stage goal.

Practical order:

1. Generate good albedo sprites.
2. Export stable accepted sprite sets.
3. Add normal/depth derivation.
4. Validate in Godot lighting.

## Test Plan

Test in small slices.

### Slice 1: Install And Identity

- Manager shows `Nymphs Sprite`, not `Sprite Foundry`.
- Module card logo/accent is purple for Nymphs Sprite.
- Details page has `Open UI`, `Open Outputs`, `Kill`, and `Logs`.
- `Kill` belongs on the Manager details pane, not only inside the custom UI.

### Slice 2: UI Sanity

- UI opens at `http://127.0.0.1:8098/nymph`.
- Sidebar shows Runtime, Character, Guide, Style, Generate, Review.
- The body does not duplicate the top header/title unnecessarily.
- `Start` text fits in the Runtime row.
- Status panel should not show `Could not read module status`.
- LoRA dropdown should populate from `$HOME/LoRA/loras`.

### Slice 3: Current Z-Image Path

- Start backend.
- Confirm Z-Image backend status is readable.
- Confirm LoRA list loads.
- Generate one small 8-way set without ControlNet refs if ControlNet wiring is
  not ready yet.
- Confirm outputs land under `$HOME/NymphsData/outputs/nymphs-sprite`.

### Slice 4: Guide Preview

- Choose each body type.
- Generate guide contact sheet.
- Confirm guide files are deterministic and visible.
- Confirm the user can understand that guides become ControlNet refs.

### Slice 5: ControlNet Wiring

- Send one guide into Z-Image ControlNet.
- Compare no-guide vs guide output.
- Confirm the guide meaningfully affects pose/shape.
- Record best default guide strength.

### Slice 6: 8-Direction Control

- Generate all 8 directions with guides.
- Verify direction read, consistency, and silhouette.
- Record failures by body type and LoRA.

### Slice 7: Audition

- Generate multiple candidates for one direction.
- Select a winner in the strip.
- Regenerate a rejected direction.
- Keep accepted directions stable.

### Slice 8: Export

- Export accepted set.
- Verify manifest, filenames, dimensions, and game import shape.

## Immediate Next Implementation Order

1. Test/update installed Nymphs Sprite `1.2.12` in the `NymphsCore` test WSL.
2. Confirm status panel and LoRA dropdown are fixed after restart/update.
3. Generate a tiny current-path 8-way set to validate output ownership.
4. Implement real guide preview generation.
5. Wire one guide image into Z-Image ControlNet.
6. Expand to 8-direction guided generation.
7. Add audition/regenerate UX using a Nymphs Image-style preview strip.
8. Revisit Godot/depth/normal export once albedo sets are reliable.

## Known Good Checks

From the dev source repo:

```bash
bash -n scripts/*.sh
python3 -m py_compile pipeline/foundry_gen_nymphscore.py scripts/sprite_foundry_ui_server.py
python3 -m json.tool nymph.json
```

From the test WSL installed module:

```bash
/home/nymph/Nymphs-Sprite/scripts/sprite_foundry_status.sh | sed -n '1,80p'
curl -sS --max-time 4 http://127.0.0.1:8098/api/status | sed -n '1,80p'
find /home/nymph/LoRA/loras -maxdepth 3 -type f -name "*.safetensors"
```

Expected current status signs:

```text
id=nymphs-sprite
version=1.2.12 or newer
controlnet_ready=true
models_ready=true
lora_choices=...
selected_lora_path=...
zimage_installed=true
```

## Do Not Forget

- Keep `sprite-foundry` locally on dev as reference.
- Keep the active module repo as `nymphs-sprite`.
- Keep the module name as `Nymphs Sprite`.
- Keep outputs owned by Nymphs Sprite even when using Nymphs Image/Z-Image.
- Keep the everyday UI simple.
- Keep experimental flows available only as reference or Advanced tools until
  they prove they make better sprites.
- A working 8-direction generator matters more than preserving every old
  Foundry feature.
