# Nymphs Sprite Distillation Plan

Current as of 2026-06-15.

This is the single current handoff for Nymphs Sprite. The old Sprite Foundry
docs remain useful reference material, but this doc is the clean resume point
for the new module.

## North Star

Nymphs Sprite should be a slick, reliable sprite-set generator for games.

The old Sprite Foundry project had good ideas, but it exposed too many
experimental paths at once. Nymphs Sprite should distill the strongest parts
into a dependable workflow:

```text
Character -> Pose Lab -> Style -> Generate -> Review -> Export
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
Nymphs Sprite 1.2.37
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

Final sprites, guide refs, review artifacts, accepted sets, exports, and
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

## Generate Optional Maps UI

Depth/normal maps are an optional part of the single Generate flow, not a
second user action.

Sidebar order:

```text
1. Character
2. Pose Lab
3. Style
4. Generate
   [collapsed] Optional Outputs
     [x] Pixelated final sprites
       Sprite Size
       Palette
     [ ] Depth/normal maps
     Map Backend: Depth Anything / MiDaS
     Map Source: Pre-pixel cutout / Final sprite / Raw image
   [Generate Sprite Set]
5. Review
```

Runtime order when maps are enabled:

```text
Nymphs Sprite UI -> foundry_generate
Nymphs Sprite pipeline generates sprites through Nymphs Image / Z-Image
Nymphs Sprite postprocess saves cutouts and sprites
Nymphs Sprite derive-maps runs from the selected source, default cutout
UI shows the normal sprite outputs plus map_review.png in the same batch strip
```

Keep this as one Generate button. The map controls are deliberately collapsed
inside Generate because they are optional outputs from the same run.

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

Current ControlNet + LoRA stance:

```text
Nymphs Sprite default: controlnet_lora_mode=on
Required backend: Nymphs Image / Z-Image 0.1.114 or newer
Runtime shape: one controlnet_edit request per direction
Payload: Pose Lab control image + selected LoRA in the same Z-Image request
Fallback: staged is diagnostic only, not the normal product path
```

This matters for performance and correctness. With the same model/rank/precision
selected, Z-Image should load the Nunchaku ControlNet pipeline once, then reuse
that already-loaded backend for every direction in the sprite run. Repeated
pipeline switching usually means an old Sprite install is still forcing staged
mode, or the test WSL has not updated Nymphs Image to `0.1.114+`.

The custom UI status panel should now read the local `/api/status` endpoint
first, then fall back to the Manager bridge only if local status fails. This was
changed in `1.2.12` because the previous bridge-first path made the UI look
broken when a stale DOM reference threw during render.

## Easy Current Flow

This is the current Nymphs Sprite flow in actual execution order.

The simplest mental model:

```text
1. Nymphs Sprite UI
   Browser / HTML / JS
   You choose character, edit Pose Lab, click Generate.

2. Nymphs Sprite module server
   Python
   Receives the UI request and runs the sprite pipeline.

3. Nymphs Sprite Pose Lab prep
   Python + Pillow
   Converts Pose Lab JSON into temporary OpenPose-style control images.

4. Nymphs Image / Z-Image backend
   Separate backend service
   This is where the AI generation happens:
   Z-Image Turbo + Nunchaku + ControlNet + LoRA.

5. Nymphs Sprite postprocess
   Python + Pillow
   Takes Z-Image's raw output and does:
   background keying, crop, square normalize, pixelate.

6. Nymphs Sprite UI
   Browser / HTML / JS
   Shows raw images, processed sprites, contact sheets, review/export controls.
```

In this section, "Sprite Python" means the Python code inside:

```text
/home/nymph/NymphsModules/nymphs-sprite
```

The main generation/postprocess script is:

```text
pipeline/foundry_gen_nymphscore.py
```

### A. Before Generate

```text
1. User chooses character/prompt/settings       [Nymphs Sprite UI / browser]
2. User edits Pose Lab direction slots          [Nymphs Sprite UI / browser]
3. Pose Lab live rig data exists as JSON        [Nymphs Sprite UI + Sprite Python]
4. User clicks Generate Sprite Set              [Nymphs Sprite UI]
5. Sprite command starts/uses Z-Image backend   [Sprite Python -> Z-Image backend]
```

Pose Lab JSON is the editable source of truth. The preview strip renders this
JSON live. Persistent PNG piles are not the design goal.

### B. Generate Loop

Nymphs Sprite then processes directions one at a time.

For every selected direction:

```text
1. Read that direction's Pose Lab JSON slot      [Sprite Python]
2. Render temp OpenPose PNG/data URL             [Sprite Python + Pillow]
3. Build Z-Image payload                         [Sprite Python]
4. Send payload to Z-Image                       [Sprite Python -> Z-Image backend]
5. Generate raw image                            [Z-Image Turbo / Nunchaku]
6. Move raw image into Sprite output folder      [Sprite Python]
7. Optional: run Sprite postprocess              [Sprite Python + Pillow]
8. If postprocess is on: key background          [Sprite Python + Pillow]
9. If postprocess is on: crop/normalize square   [Sprite Python + Pillow]
10. If postprocess is on: save pre-pixel cutout  [Sprite Python + Pillow]
11. Optional: pixel resize to sprite size        [Sprite Python + Pillow]
12. Save final direction PNG                     [Sprite Python]
13. Move to next direction                       [Sprite Python]
```

The Z-Image payload is normally:

```text
mode: controlnet_edit
input image: temporary Pose Lab OpenPose PNG/data URL
prompt: character/style prompt with pose language stripped back
LoRA: selected LoRA in the same ControlNet request
output_dir: Nymphs Sprite backend staging folder
```

The normal product path is same-pass ControlNet + LoRA. The old staged path was
a temporary diagnostic workaround from the broken-backend period; keep it only
for isolating regressions.

Raw direction output is moved to:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject>/<direction>_raw.png
```

Processed direction output is saved to:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject>/<direction>.png
```

Important output distinction:

```text
<direction>_raw.png
  Direct Z-Image result. Use this to judge generation, ControlNet, LoRA,
  prompt, and pose following.

_intermediate/<direction>_cutout.png
  Raw image after Nymphs Sprite background keying, crop, and square normalize.
  Use this to judge cutout/crop quality before sprite crunching.

<direction>.png
  Final visible output in the UI strip. If "Postprocess sprites" is off, this
  is the raw Z-Image result copied into the normal final slot. If postprocess
  is on and "Pixel resize final sprites" is off, this is the normalized cutout.
  If both are on, this is resized to Sprite Size with nearest-neighbor.
```

Postprocess is optional because the simple key/crop/normalize path can hide
whether Z-Image + ControlNet + LoRA worked. Turn it off to inspect raw model
results through the normal UI strip. Pixel resize is separately optional
because it can make a weak raw image look much worse in the preview. Turn it
back on when judging actual game-sprite scale.

When postprocess is off, no `_intermediate/<direction>_cutout.png` files are
created and Foundry registration records only raw/final artifacts for each
direction.

Pre-pixel cutout output is saved to:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject>/_intermediate/<direction>_cutout.png
```

Raw images are the best place to judge whether ControlNet, prompt, and LoRA
worked. The processed direction PNG is where background removal, cropping, and
pixelation can introduce separate problems.

### C. After All Directions

After the direction loop finishes:

```text
1. Build raw inspection sheet                    [Sprite Python + Pillow]
2. Build processed contact sheet                 [Sprite Python + Pillow]
3. Write recipe metadata                         [Sprite Python]
4. Write manifest metadata                       [Sprite Python]
5. Register attempts/review records              [Sprite Python + local DB]
6. UI gallery shows the newest output folder      [Nymphs Sprite UI]
```

### Current Background Removal

Backend: Nymphs Sprite Python + Pillow.

Current background removal is not BRIA/RMBG and not a learned matting model.

It is a simple local keyer in:

```text
pipeline/foundry_gen_nymphscore.py
```

The current function:

- samples the four image corners to estimate background color
- removes pixels close to that background color
- also removes obvious green-screen pixels

This happens immediately after each raw direction image is generated and moved
into the Sprite output folder, before crop/normalize/pixelate.

This is deliberately crude and is the weak stage right now. It can leave halos,
eat edges, fail on green spill, or behave badly when the model paints uneven
backgrounds.

### BRIA/RMBG Next Step

Future backend: likely Pixal3D BRIA/RMBG code path or a shared local RMBG helper.

BRIA/RMBG should replace or supplement the current simple keyer after the current
ControlNet/LoRA flow is validated.

The intended future per-direction postprocess would become:

```text
raw generated direction image
  -> BRIA/RMBG alpha matte
  -> optional alpha cleanup
  -> crop/normalize
  -> pixelate
  -> final direction sprite
```

Pixal3D already has BRIA/RMBG wiring, so the next investigation is whether
Nymphs Sprite should reuse that module path, share a small common RMBG helper,
or call a Pixal3D-owned background-removal action. Keep this as an optional
background-removal upgrade, not part of the first ControlNet validation.

### Depth And Normal Map Postprocess

The old Sprite Foundry did have a map postprocess, but it was not part of the
main image-generation pass.

Old Foundry map flow:

```text
accepted albedo/raw sprite
  -> upload to ComfyUI
  -> MiDaS-NormalMapPreprocessor
  -> save normal_raw + pixel normal map
  -> DepthAnythingPreprocessor
  -> save depth_raw + pixel depth map
  -> register normal/depth artifacts
  -> export albedo/normal/depth pack
```

Old source files:

```text
/home/nymph/NymphsModules/sprite-foundry/pipeline/foundry_maps.py
/home/nymph/NymphsModules/sprite-foundry/pipeline/gen_kael_maps.py
```

The same legacy files currently exist in Nymphs Sprite too:

```text
/home/nymph/NymphsModules/nymphs-sprite/pipeline/foundry_maps.py
/home/nymph/NymphsModules/nymphs-sprite/pipeline/gen_kael_maps.py
```

Current old implementation details:

- backend: ComfyUI on `http://127.0.0.1:8188`
- normal model/node: `MiDaS-NormalMapPreprocessor`
- depth model/node: `DepthAnythingPreprocessor`
- depth checkpoint: `depth_anything_vitl14.pth`
- input: accepted raw/albedo sprite artifacts from the Foundry DB
- output: `*_normal_raw.png`, `*_normal.png`, `*_depth_raw.png`,
  `*_depth.png`
- export structure: `albedo/`, `normal/`, `depth/`, `preview/`,
  `manifest.json`

This is a good idea to keep, but not as-is. It is still wired to old Foundry
state, ComfyUI, and `bakeoff/` folders.

Recommended Nymphs Sprite adaptation:

```text
Generate/review sprite set
  -> accept/select final direction sprites
  -> optional Maps stage
  -> create normal/depth maps from the accepted clean sprite images
  -> show a 3-row review sheet: albedo / normal / depth
  -> export game pack with albedo, normal, depth, manifest
```

Best near-term product shape:

```text
Review
  -> Export
     - Albedo only
     - Albedo + Depth
     - Albedo + Normal + Depth
     - Godot pack
```

Do not block the core sprite generator on maps. Treat depth/normal generation as
an optional export enhancement after the sprite image, cutout, crop, and
pixelation stages are already accepted.

Implemented model-backed slice:

```text
python -m foundry.cli derive-maps --subject <subject> --direction-count 8 --source cutout --backend depth_anything --sprite-size 96
```

Implementation file:

```text
/home/nymph/NymphsModules/nymphs-sprite/pipeline/nymphs_sprite_maps.py
```

Current backend:

```text
depth_anything
```

`depth_anything` is a ComfyUI-free real model path using Transformers depth
estimation directly in Python.

Supported backends:

```text
depth_anything -> LiheYoung/depth-anything-small-hf
midas          -> Intel/dpt-hybrid-midas
alpha_volume   -> explicit emergency/debug fallback only
```

The model-backed path:

- reads pre-pixel cutout direction PNGs from the Nymphs Sprite output folder
- composites transparent cutouts for the RGB-only depth model
- generates depth with the selected model backend
- normalizes depth over the foreground alpha only
- derives a normal candidate from the depth gradient
- writes `albedo/`, `depth/`, `normal/`, `map_review.png`, and `manifest.json`

Model cache:

```text
$HOME/NymphsData/cache/huggingface
```

Model fetching:

```text
Details page -> Model Fetch -> Nymphs Sprite Map Models
```

Equivalent direct command:

```text
scripts/sprite_foundry_fetch_controlnet.sh --model nymphs_sprite_map_all
```

Fetch profiles:

```text
nymphs_sprite_map_all
nymphs_sprite_map_depth_anything
nymphs_sprite_map_midas
```

Validation on dev WSL:

```text
Depth Anything:
/home/nymph/NymphsData/outputs/nymphs-sprite/goblin_scout/maps/20260612-162653/map_review.png

MiDaS:
/home/nymph/NymphsData/outputs/nymphs-sprite/goblin_scout/maps/20260612-162853/map_review.png
```

Current map-source decision:

```text
Maps should be derived after cutout/normalization and before pixelation.
```

Reason:

- original Foundry uploaded high-resolution raw accepted images to ComfyUI
  preprocessors first, then pixelated the resulting depth/normal maps down to
  the sprite target
- final 96px sprite PNGs have already thrown away detail, so they are a worse
  source for depth/normal
- raw generated images still include background and can be fully opaque, so
  they are also a worse source until BRIA/RMBG is available
- use pre-pixel cutouts now, and later replace the current simple keyer with
  BRIA/RMBG for better cutout inputs
- then crop/normalize/pixelate the generated maps to match the final albedo
  sprite size
- keep final map alignment strict: every `albedo/<direction>.png` must have
  matching `normal/<direction>.png` and `depth/<direction>.png`

### Future Texture/PBR Module Boundary

There is a related but separate idea: a dedicated Nymphs texture/material module
based on the kind of flow shown by:

```text
https://github.com/lovisdotio/fal-texture-pbr-generator
```

That repo is a PATINA/fal.ai-style PBR texture generator. Its README describes
text-to-material and image-to-PBR workflows, real-time Three.js preview, and
downloads for standard maps such as `BaseColor`, `Normal`, `Roughness`,
`Metallic`, and `Height`.

This should probably become a separate module, not extra weight inside Nymphs
Sprite.

Possible future module:

```text
Nymphs Texture
  -> text or image input
  -> PBR material maps
  -> 3D preview
  -> Substance/Blender/Unreal/Unity/Godot export
```

Relationship to Nymphs Sprite:

- Nymphs Sprite owns character sprite sheets, Pose Lab, direction control,
  sprite cutout, pixelation, and game-sprite export.
- Nymphs Texture owns tileable materials, PBR maps, texture previews, and
  material pack export.
- A future bridge could let Sprite export albedo/normal/depth packs while
  Texture handles richer PBR material generation for environments, props, and
  surfaces.

Keep the boundary clean. Sprite can have optional depth/normal export for game
lighting, but full PBR material generation belongs in a separate texture module.

Better shared-module framing:

```text
Nymphs Texture / Map Lab
  -> shared map generation service for all modules
  -> text-to-PBR materials
  -> image-to-PBR extraction
  -> normal/height/roughness/metallic/basecolor packs
  -> map preview and export
  -> callable from Sprite, Pixal3D, TripoSplat, TRELLIS, and future mesh modules
```

Useful parts from `fal-texture-pbr-generator`:

- simple `/api/generate` pattern with `text` and `image` modes
- map request list: `basecolor`, `normal`, `roughness`, `metalness`, `height`
- result normalization into a stable map dictionary
- live Three.js material preview
- material sliders for displacement, normal intensity, metalness, roughness, and
  environment/reflection strength
- ZIP/export naming conventions for external tools

Important distinction:

```text
PBR height map != always the same as character/object depth map
```

PBR height is usually surface relief or displacement for a material. Character
depth is object-space or view-relative volume information for sprite/game
lighting. They can both be useful, but Nymphs Sprite should not blindly treat a
PATINA `height` map as a perfect Sprite `depth` map without testing.

Good interception points:

```text
Sprite accepted albedo
  -> Map Lab image-to-PBR
  -> use normal/height candidates for lighting experiments
  -> compare against old DepthAnything/MiDaS map stage

Pixal3D/TRELLIS/TripoSplat mesh texture
  -> Map Lab image-to-PBR or text-to-PBR
  -> apply basecolor/normal/roughness/metallic/height to mesh materials

World/prop/environment modules
  -> Map Lab text-to-PBR
  -> tileable material packs
```

Preferred architecture:

```text
Nymphs Texture / Map Lab owns PBR generation.
Other modules call it as a service.
Each caller decides how to use the maps.
```

This keeps Nymphs Sprite lean while still allowing Sprite to request better
normal/depth/height candidates during export.

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

This path uses Z-Image / Nunchaku / LoRA for generation. Pose Lab JSON refs are
now saved before Generate, rendered as temporary in-memory OpenPose control
PNGs, and passed into Z-Image as `controlnet_edit` inputs per direction.

The next milestone is empirical: confirm Z-Image follows the refs strongly
enough, tune the default OpenPose proportions/strength, and compare guided vs
unguided outputs.

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
2. Choose 8 or 16 directions.
3. Edit the live direction slots in the normal preview strip.
4. Select the direction slots to include.
5. Generate the sprite set using those guides through Z-Image ControlNet.

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

### Pose Lab

The first implemented ControlNet workflow is `Pose Lab`. It exists to make
clean reusable refs, not to become a large second product.

Keep this simple:

```text
Pose Lab settings -> edit live direction slots -> select slots -> commit JSON refs
```

The default OpenPose Skeleton path is local and deterministic. It does not ask
another image model to invent an OpenPose map. The UI owns a small editable rig:

- one page
- opens in the main preview area as a large pose workbench
- one active direction at a time
- the normal preview strip becomes the 8/16 live direction-slot selector
- clicking a slot changes the active editor slot
- checking a slot marks it for commit/generation
- each direction saves its own joint positions
- drag colored points to move joints
- Move Points is the default mode and moves only the selected joint
- Keep Lengths is an optional IK helper for wrists and ankles
- Reset restores the active direction
- Mirror mirrors the active direction
- Copy All copies the active pose into every direction slot

When `Commit Refs` is pressed, Nymphs Sprite stores the editable pose set as
`pose_set.json`. The JSON contains all direction slots and the selected
direction list. The browser renders live strip thumbnails directly from the
JSON. Black-background OpenPose PNG maps are rendered only on demand when the
generation backend needs ControlNet inputs; they are temporary handoff data,
not the source of truth.

Committed sets live in Nymphs Sprite-owned outputs:

```text
$HOME/NymphsData/outputs/nymphs-sprite/pose_lab/refs/<subject>/<timestamp>/
```

Pose Lab should own every future ControlNet prep lane, but only OpenPose is
visible in the simple working UI right now. Future ref types:

- OpenPose Skeleton: local editable rig; default first-class path for pose and
  limb control.
- Canny / Line: useful for silhouette and outline fidelity.
- Scribble: useful for rough shape and body mass experiments.
- Depth Mass: later research path for simple grayscale volume cues.

Ref management should remain lightweight for now:

- live Pose Lab slots appear in the normal gallery/preview strip while Pose Lab
  is open
- committed refs appear as one JSON pose-set card
- `View Refs` jumps to the newest committed Pose Lab folder
- clicking a committed pose-set thumbnail reloads the saved pose set into the
  editor
- checking live direction slots selects them for future generation wiring or
  contact sheet export
- do not build a large ref database yet
- do not add a premade pose preset library until the rig editor feels excellent

Future promotion path:

```text
pose_lab/refs/<subject>/<timestamp>/
  -> pose_lab/presets/<body>/<control_type>/<8way-or-16way>/
```

Only add the preset promotion button after real test results show which pose
refs are worth keeping.

## Best Working Flow To Build First

Build and test from the top down.

### 1. Character

- Pick a preset or write a prompt.
- Set subject ID.
- Keep prompt and negative prompt visible.
- Prompt presets are test fixtures, not the whole product.

### 2. Pose Lab

- Pick body type.
- Pick 8 or 16 directions.
- Commit OpenPose refs from the editable rig.
- Keep Canny/line, scribble, and depth-mass as future Pose Lab lanes.
- Show committed refs in the preview strip.
- Save guide files under Nymphs Sprite outputs/tmp.

### 3. Style

- Pick LoRA.
- Style controls are model/style inputs, not Python pixelation.
- Keep advanced model/rank/seed/step controls available but not dominant.

### 4. Generate

- Generate all selected directions through Z-Image.
- Use Pose Lab body/direction guides as ControlNet refs.
- Optional Outputs contains postprocess/export extras:
  Sprite postprocess, pixel resize, sprite size, palette, and depth/normal maps.
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

16 directions are now exposed as an option for Pose Lab and the Z-Image
generation runner. Use 8 directions as the default test path. Use 16 when the
extra angular coverage is worth roughly doubling the generation cost.

16 directions:

```text
front
front_front_left
front_left
left_front_left
left
left_back_left
back_left
back_back_left
back
back_back_right
back_right
right_back_right
right
right_front_right
front_right
front_front_right
```

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

The preview strip should stay folder-scoped after generation. Avoid dumping the
entire `Recent` history into the strip after a run; it gets too noisy. New
sprite runs should show the newest subject/run folder. New Pose Lab commits
should show the newest committed ref folder. Contact sheets are optional exports
from selected thumbnails, not the ControlNet input format.

## Godot / Packaging

Godot export remains a real goal, but should not block the first reliable
generator.

Target export contents:

- accepted direction PNGs
- selected direction refs
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
- Generate one small 8-way set with Pose Lab refs.
- Confirm outputs land under `$HOME/NymphsData/outputs/nymphs-sprite`.
- Confirm generation logs say `mode=controlnet`, not only `mode=txt2img`.
- Confirm the generated `recipe.json` has non-empty `controlnet_directions`.

### Slice 4: Guide Preview

- Choose each body type.
- Select 8 or 16 directions.
- Move points in one direction slot.
- Switch directions from the live preview strip and confirm each slot keeps its
  own pose.
- Check/uncheck slots and commit OpenPose JSON refs.
- Confirm `pose_set.json` contains all edited slots plus the selected direction
  list.
- Confirm no persistent PNG pile is created during Pose Lab commit.
- Confirm the user can understand that guides become ControlNet refs.

### Slice 5: ControlNet Quality

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

1. Test/update installed Nymphs Sprite `1.2.34` or newer in the `NymphsCore`
   test WSL.
2. Confirm status panel and LoRA dropdown are fixed after restart/update.
3. Open Pose Lab, move points in one direction, switch slots, and confirm the
   slot state is retained.
4. Commit Pose Lab OpenPose Skeleton refs and confirm the edited slot appears
   in `pose_set.json`.
5. Generate a Canny/Line candidate only as a secondary research check.
6. Generate a tiny guided 8-way set to validate output ownership.
7. Try one 16-way run only after the 8-way path is stable.
8. Confirm guided generation logs `mode=controlnet` for each direction.
9. Compare guided vs unguided output quality and tune default guide strength.
10. Add audition/regenerate UX using a Nymphs Image-style preview strip.
11. Revisit Godot/depth/normal export once albedo sets are reliable.

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
version=1.2.34 or newer
controlnet_ready=true
models_ready=true
lora_choices=...
selected_lora_path=...
zimage_installed=true
```

## Resume Checkpoint: 2026-06-09

Current source-of-truth repos:

- Module: `nymphnerds/nymphs-sprite`
- Dev registry: `nymphnerds/nymphs-registry`
- Reference-only old module: local `sprite-foundry` on the dev WSL

Latest target module state:

- Nymphs Sprite `1.2.34`
- Purpose: wire live Pose Lab JSON refs into Z-Image ControlNet generation.

What changed in the latest working idea:

- Pose Lab is now the single ControlNet prep system.
- Opening Pose Lab hot-swaps the main preview into the rig editor.
- The normal bottom preview strip becomes the live 8/16 direction-slot strip.
- Each strip slot renders from live JSON pose data, not from stored PNG files.
- Clicking a slot selects that direction for editing in the main rig editor.
- The checkbox on a slot marks whether that direction should be included when
  committing refs.
- `Commit Refs` writes one `pose_set.json` containing all editable slots and
  the selected direction list.
- Persistent Pose Lab PNG piles are intentionally gone. ControlNet PNG maps are
  rendered as temporary in-memory handoff images during Generate.
- Generate auto-saves the current Pose Lab JSON before calling the backend, so
  the user does not need to remember `Commit Refs` first.
- The runner records `pose_lab_ref_set`, `controlnet_directions`, and
  `controlnet_conditioning_scale` in `recipe.json` / `manifest.json`.
- Logs should show `[direction] generate seed=... mode=controlnet...` when the
  Pose Lab handoff is active.

Known untested / risky areas:

- The live 8/16 strip needs user testing after updating the installed test WSL.
- The current humanoid 8/16 default poses are procedural guesses, not proven
  sprite-quality baselines.
- The 16-way in-between poses may feel off because perspective, near/far limb
  placement, and shoulder/hip compression are only approximate.
- The best OpenPose strength/default settings for Z-Image Turbo ControlNet
  Union still need empirical testing.
- The first generated outputs before this fix were plain `txt2img`; they did
  not use Pose Lab refs and are not evidence against the Pose Lab concept.
- If a new run still ignores poses, check the run log for `mode=controlnet` and
  check `recipe.json` for `controlnet_directions`.

Next best pickup steps:

1. Update/install Nymphs Sprite `1.2.34+` on the `NymphsCore` test WSL.
2. Open Pose Lab and confirm the bottom strip immediately shows all 8 slots.
3. Switch to 16 directions and confirm all 16 live JSON slots appear.
4. Click several strip slots and confirm the main editor changes direction.
5. Move a joint in one slot, switch away, switch back, and confirm it persists.
6. Check/uncheck a few slots, commit refs, and inspect `pose_set.json`.
7. Research/build a better **Humanoid Neutral 8** baseline:
   - bottom-aligned feet
   - aligned head/shoulder/hip/foot heights
   - readable sprite silhouette
   - stable front/back/side/diagonal turn
8. Derive **Humanoid Neutral 16** from the proven 8-way set, with gentle
   in-between rotations instead of dramatic new poses.
9. Generate a tiny 8-way run and tail logs for `mode=controlnet`.
10. Inspect `recipe.json` and confirm `controlnet_directions` contains the
    generated directions.
11. Compare guided pose adherence separately from green-screen cleanup;
    green-screen is a later post-process issue.

Useful research conclusions so far:

- ControlNet wants a structural control map: OpenPose skeleton, edge map, depth
  map, etc. The prompt supplies content/style; the control map supplies layout.
- For OpenPose, body keypoints control pose and placement while mostly ignoring
  clothing and style details.
- If a hand-authored OpenPose skeleton map is already provided, the generation
  side should treat it as the control image and avoid trying to re-detect the
  pose from it.
- Sprite turnarounds should prioritize consistent alignment across views:
  head, shoulders, hips, and feet should not drift casually between directions.
- A boring, excellent neutral set is more valuable than lots of clever presets.

## Do Not Forget

- Keep `sprite-foundry` locally on dev as reference.
- Keep the active module repo as `nymphs-sprite`.
- Keep the module name as `Nymphs Sprite`.
- Keep outputs owned by Nymphs Sprite even when using Nymphs Image/Z-Image.
- Keep the everyday UI simple.
- Keep experimental flows available only as reference or Advanced tools until
  they prove they make better sprites.

## Resume Checkpoint: 2026-06-12

Current test symptom:

- A guided 8-way Goblin Scout run completed and saved all direction outputs,
  but the saved images were blue/white/black unresolved noise rather than
  sprites.
- The UI showed the run as done, and `manifest.json` confirmed the backend
  returned `mode: controlnet_edit` for every direction.
- This means the Pose Lab handoff reached Z-Image ControlNet. The failure is
  not that Pose Lab refs were missing from the runner.

Important finding:

- The recipe for the failed run used:
  `/home/nymph/LoRA/loras/tarn59_pixel_art/tarn59_pixel_art.safetensors`
  while still using the `pxlstl` trigger that belongs to the mks0813 LoRA.
- The UI/status path was showing the mks0813 LoRA, so this pointed to a stale
  or fallback LoRA path during argument assembly.
- The runner also sent `guidance_scale: 0.0` into `controlnet_edit`. Plain
  Z-Image Turbo txt2img commonly uses zero guidance, but the known
  ControlNet-edit notes used CFG/guidance around `1.0`.

Patch direction for `1.2.22`:

- Do not silently fall back to the latest LoRA reported by Z-Image. If no LoRA
  path is supplied, fail clearly and ask the user to choose one.
- Build the generate args from the actual selected LoRA dropdown option so the
  payload matches what the UI shows.
- Keep normal txt2img guidance at `0.0`, but send ControlNet generations with
  a stronger dedicated `controlnet_guidance_scale`.
- Record `controlnet_guidance_scale` in `recipe.json`.

Follow-up patch for `1.2.23`:

- A test run exposed that `foundry_generate` could still receive no LoRA path
  from the UI/Manager action args.
- The generate action now has a deterministic Nymphs Sprite LoRA fallback:
  prefer bundled mks0813, then SkyAsl, then tarn59, then the first local
  `.safetensors` under `$HOME/LoRA/loras`.
- This fallback also assigns the known trigger for bundled LoRAs.
- This is intentionally different from the removed Z-Image `/api/loras`
  fallback: it does not ask the backend for its latest/random LoRA and should
  avoid the previous tarn59 + `pxlstl` mismatch.

Follow-up patch for `1.2.24`:

- The real Manager action launches through `foundry.cli generate-nymphscore`,
  not directly through `pipeline/foundry_gen_nymphscore.py`.
- `1.2.22` added `--controlnet-guidance-scale` only to the pipeline parser, so
  the CLI-created `Namespace` lacked `controlnet_guidance_scale` and crashed
  before the garbled-output fix could be tested.
- Added the missing CLI arg and a defensive runner default. This was later
  raised to `4.0` during ControlNet noise testing.

Next validation:

1. Update the test WSL to Nymphs Sprite `1.2.24`.
2. Start Z-Image fresh if the backend gets wedged after a failed run.
3. Run the same 8-way Goblin Scout set.
4. Confirm the new `recipe.json` uses the selected mks0813 LoRA path and
   `lora_trigger: pxlstl`.
5. Confirm `controlnet_directions` contains all generated directions.
6. Confirm `controlnet_guidance_scale` is `4.0`.
7. If outputs are still unresolved noise, isolate with a no-LoRA direct
   `controlnet_edit` probe before blaming Pose Lab. If no-LoRA also produces
   noise, investigate the Z-Image ControlNet runtime/adaptation. If no-LoRA
   works, investigate LoRA + ControlNet interaction and scale.
- A working 8-direction generator matters more than preserving every old
  Foundry feature.

## Resume Checkpoint: 2026-06-12 ControlNet Noise Deep Dive

The `1.2.24` crash fix got generation running again, but the next user test
still produced full-frame blue/white/black checker-noise during
`controlnet_edit`.

Working assumption:

- This is a ControlNet runtime/payload problem, not the pixelation stage.
- The raw images are already corrupted before green-screen removal, crop, and
  nearest-neighbor sprite resizing.
- The old non-ControlNet Z-Image path worked, so do not chase general prompt or
  LoRA availability first.

Research findings:

- The Z-Image Turbo ControlNet Union 2.1 2602 weight explicitly supports Pose,
  Canny, Depth, MLSD, HED, Scribble, and Gray.
- The model card says the 2.1 8-step family should use 8 inference steps and
  a ControlNet/control-context strength in the `0.65-1.00` range.
- Diffusers Z-Image guidance only enables classifier-free guidance when
  `guidance_scale > 1`.
- The official Z-Image-Fun ControlNet example uses a stronger guided setting
  than our `1.0` default.
- Classic ControlNet OpenPose maps are colored sticks/keypoints on black, so
  the Pose Lab renderer should stay OpenPose-like for now. Monochrome refs are
  a future Scribble/Canny experiment, not the default Pose path.

Current prompt rule:

- LoRA owns style.
- Pose Lab owns pose and direction when ControlNet refs exist.
- The generation payload strips inherited style clauses before sending prompts
  to Z-Image: no `pixel art`, `sprite`, `HD-2D`, `48px`, green-screen,
  photorealistic, 3D-render, smooth/blurry, or similar style-fighting text.
- The final positive prompt is intentionally small:
  LoRA trigger + cleaned character identity + no-background/no-shadow output
  constraints + Pose Lab control instruction.
- The final negative prompt keeps mechanical exclusions and adds no background,
  no floor/ground plane, no cast/drop/contact shadow.
- ControlNet guidance stays at `0.0`; do not reintroduce the old CFG-4
  experiment unless a fresh backend test proves it is needed.

Useful diagnostic flags remain:

- `--controlnet-mode off`
- `--debug-no-lora`
- `--max-directions N`

Immediate test matrix:

1. `txt2img + LoRA`, one direction:
   `--controlnet-mode off --max-directions 1`
2. `ControlNet without LoRA`, one direction:
   `--debug-no-lora --max-directions 1`
3. `ControlNet + selected LoRA`, one direction:
   default mode, `--max-directions 1`

Interpretation:

- If test 1 works and test 2 is noise, the Z-Image/Nunchaku ControlNet runtime
  or ControlNet weight integration is broken.
- If tests 1 and 2 work but test 3 is noise, the problem is LoRA + ControlNet
  interaction, probably LoRA merge/rank/scale in the Nunchaku ControlNet
  pipeline.
- If all three work at one direction but the full 8-way run fails, look at
  backend state reuse, batch staging, or per-direction payload differences.

## Probe Results: 2026-06-12

Local dev probes were run against Z-Image foreground API with the Nunchaku
environment sourced from `scripts/_zimage_common.sh`. Important: launching
`api_server.py` directly without that environment starts the standard runtime
and reports `supports_controlnet_edit: false`.

Probe setup:

- subject: `goblin_scout`
- size: `512x512`
- steps: `8`
- direction: `front` only via `--max-directions 1`
- diagnostic pose set:
  `$HOME/NymphsData/outputs/nymphs-sprite/pose_lab/refs/goblin_scout/diagnostic-current/pose_set.json`

Results:

1. `txt2img + mks0813 LoRA`, no ControlNet:
   `--controlnet-mode off`
   produced a normal goblin scout image. This proves base Z-Image/Nunchaku +
   LoRA generation is healthy.

2. `ControlNet`, no LoRA:
   `--debug-no-lora`
   produced a non-noisy but blurry dark humanoid silhouette. This proves the
   ControlNet path can return a real image without LoRA, but it also proves the
   current Pose Lab ref is not being followed strongly enough for production.

3. `ControlNet + mks0813 LoRA`:
   `lora_scale=1.0`
   produced full-frame checker/noise. This reproduces the user failure with the
   selected mks0813 pixel-art LoRA.

4. `ControlNet + SkyAsl LoRA`:
   `lora_scale=1.0`
   also produced full-frame checker/noise. This means the corruption is not
   mks0813-specific. It is a general LoRA + Z-Image ControlNet/Nunchaku
   interaction.

5. `ControlNet + mks0813 LoRA`:
   `lora_scale=0.25`
   still produced full-frame checker/noise. This means the corruption is not
   just a too-strong LoRA scale. Any active LoRA in this ControlNet/Nunchaku
   path should be treated as unsafe until the backend merge path is fixed.

6. `ControlNet with selected LoRA bypassed for the ControlNet payload`:
   the user can still choose a LoRA in Nymphs Sprite, but the runner strips
   `lora_path`/`lora_scale` only when it sends `mode=controlnet_edit`.
   This produced a real non-noisy goblin image and the backend log confirmed
   `lora=False` plus `wrapper.reset` before denoising.

Split the bugs:

- Bug A: LoRA + ControlNet corrupts image quality. This is likely in the
  Nunchaku Z-Image ControlNet LoRA merge/deferred wrapper path, not in Pose Lab.
  The temporary safety fix was to bypass LoRA only for `controlnet_edit` calls.
  A later live dev test proved same-pass ControlNet + quantized Nunchaku LoRA
  still corrupts output even after the backend LoRA sync patch.
- Bug B: Pose obedience is weak even when ControlNet does not corrupt. This is
  a separate control-image-format/strength problem. The current Pose Lab PNG is
  transported correctly, but it is not proven to be the best format for this
  Z-Image Union ControlNet.

ControlNet + LoRA target behavior:

- `controlnet_lora_mode` now defaults to `on`.
- The normal path sends Pose Lab refs through `controlnet_edit` with the
  selected LoRA in the same backend request.
- `--controlnet-lora-mode staged` remains only as a diagnostic fallback from
  the broken-backend period.
- `--controlnet-lora-mode off` remains a no-LoRA diagnostic fallback.
- `recipe.json` records `controlnet_lora_mode` so a bad run can be traced
  without guessing which path was active.

Next technical probes:

1. Test `controlnet_conditioning_scale=1.0` no-LoRA to see if pose obedience
   improves without introducing noise.
2. Compare OpenPose-color refs against a simple Scribble/edge silhouette ref,
   because this diffusers pipeline has no explicit `pose` mode flag; it
   VAE-encodes the control PNG as visual context.
3. If same-pass regresses, isolate with `--controlnet-lora-mode off` and
   `--controlnet-lora-mode staged --max-directions 1` before changing the
   normal product path again.

## Patch Checkpoint: 2026-06-12 Pose Lab Prompt Authority

The next failure after the ControlNet noise split was simpler and important:
the character prompts were fighting Pose Lab. For example, Goblin Scout asked
for a "deep predatory crouch" while the active Pose Lab ref was upright. The
negative prompt also blocked "standing upright", which directly punished the
ref we were trying to follow.

Current rule:

```text
When a Pose Lab ref is active, Pose Lab owns pose, stance, limb placement,
silhouette, and direction. The character prompt owns identity, clothing,
materials, palette, and readable sprite style.
```

Implemented fix:

- `pipeline/foundry_gen_nymphscore.py` now sanitizes prompt clauses only when a
  ControlNet/Pose Lab image is active.
- The sanitizer removes pose/action/view clauses such as crouch, stance,
  standing, leaning, hands, arms, feet, profile view, facing, and similar
  control-conflict language.
- The sanitizer keeps identity/style clauses such as goblin, hood, glowing
  eyes, armor, cloak, material, color, and creature description.
- The generated positive prompt now includes an explicit mandatory Pose Lab
  control-reference instruction.
- The generated negative prompt now blocks only "does not match the control
  reference" style failures, instead of globally banning concrete poses that
  the user may intentionally draw later.
- `verify.sh` now has a Pose Lab prompt hygiene regression check.

Example sanitized Goblin Scout identity prompt:

```text
solo, 1character, single character only, one figure, a goblin scout assassin,
dark tattered hood pulled low over face hiding features except two glowing pale
yellow eyes peering out, lean compact body wrapped in a dark grey-brown ragged
cloak that breaks the body outline, mottled dark green skin barely visible
under wrappings, dark cloth wraps around forearms and shins, fully visible full
body
```

Local validation:

- `bash -n scripts/sprite_foundry_generate.sh`: passed.
- `python -m py_compile pipeline/foundry_gen_nymphscore.py foundry/cli.py`:
  passed.
- Z-Image backend touched files `model_manager.py` and `nunchaku_compat.py`:
  passed `py_compile`.
- `PYTHON_BIN=/home/nymph/Z-Image/.venv-nunchaku/bin/python bash verify.sh`:
  passed, including the new prompt hygiene check.

Backend note:

- `/home/nymph/Z-Image/nunchaku_compat.py` was also patched to avoid replacing
  Nunchaku's own modern `forward` method when that method already supports
  `controlnet_block_samples` and `**kwargs`.
- A diagnostic `ControlNet + LoRA` retest after that first patch still hung
  after the backend request went quiet, with no fresh output written. That was
  before the later backend LoRA synchronization fix below.

Follow-up backend integration fix:

- `/home/nymph/Z-Image/model_manager.py` had another likely ControlNet/LoRA
  ordering bug.
- The Nunchaku transformer is wrapped in `DeferredNunchakuLoraWrapper`, which
  normally waits until `transformer.forward()` to apply/reset LoRA weights.
- In `ZImageControlNetPipeline`, the ControlNet forward runs before the
  transformer forward. That means ControlNet could produce
  `controlnet_block_samples` from the old/no-LoRA transformer state, then the
  transformer would suddenly apply LoRA on its own forward pass.
- This mismatch was a real bug, but live testing later proved it was not the
  whole checker-noise cause.
- `model_manager.py` now forces the deferred wrapper to synchronize immediately
  when configuring or resetting LoRA on a pipeline that has `controlnet`, so
  ControlNet and the transformer see the same LoRA state before denoising.
- Live dev WSL validation showed same-pass `controlnet_edit + LoRA` still
  produces checker/noise.

## Patch Checkpoint: 2026-06-12 Staged ControlNet + LoRA

Dev WSL live testing narrowed the garble to Nunchaku's quantized Z-Image LoRA
application during a ControlNet denoise pass:

- Pose Lab `front_control.png` was clean OpenPose-style skeleton data.
- `controlnet_edit` without LoRA produced a real goblin silhouette.
- Same-pass `controlnet_edit` with mks0813 LoRA produced checker/noise even at
  `controlnet_guidance_scale=1.0`.
- Restarting the backend with
  `NYMPHS_ZIMAGE_LORA_DISABLE_QUANTIZED=1` stopped the checker/noise. The log
  changed from `updated_lora_modules: 136` to `updated_lora_modules: 0`.
- That proves the corruptor is the quantized Nunchaku LoRA path inside the
  same ControlNet denoise call. It also means that switch is not a product fix,
  because it disables the LoRA effect.

Temporary staged diagnostic path from this checkpoint:

```text
Pose Lab JSON
  -> temporary OpenPose PNG
  -> Z-Image controlnet_edit with no LoRA
  -> posed raw image
  -> Z-Image img2img with selected LoRA
  -> final raw sprite source
  -> pixelate/export
```

Historical behavior from this checkpoint:

- `--controlnet-lora-mode staged` was made the default during this checkpoint.
- `staged` saves `<direction>_pose_raw.png` for the first ControlNet stage.
- Final `<direction>_raw.png` comes from the second LoRA img2img stage.
- `--lora-img2img-strength` defaults to `0.45`.
- `--controlnet-lora-mode on` still exists only for same-pass backend testing.
- `--controlnet-lora-mode off` skips the LoRA refinement.

Dev WSL validation:

- One-direction staged Goblin Scout run completed.
- Backend logs showed first call `mode=controlnet_edit lora=False`.
- Backend logs showed second call `mode=img2img lora=True`, with the selected
  mks0813 LoRA applied to 136 quantized modules.
- Final output was not checker/noise. It is still soft and needs tuning, but
  the catastrophic corruption is gone.

Current generation stance has since changed back to same-pass by default after
the Z-Image `0.1.114` packed-LoRA compatibility fix. Keep this section as
forensic history only.

Docs/source anchors for the next resume:

- Z-Image Turbo ControlNet Union 2.1 model card:
  `https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1`
- Diffusers Z-Image ControlNet pipeline docs:
  `https://huggingface.co/docs/diffusers/main/en/api/pipelines/z_image`
- VideoX-Fun native Z-Image ControlNet example:
  `https://github.com/aigc-apps/VideoX-Fun/blob/main/examples/z_image_fun/predict_t2i_control_2.1.py`

## Patch Checkpoint: 2026-06-12 Same-Pass Backend Garble Attempt

The checker/noise bug was not caused by Pose Lab PNG generation. It was caused
by our Z-Image Nunchaku compatibility shim.

Root cause:

- Pose Lab refs rendered clean OpenPose-style PNGs.
- ControlNet without LoRA produced a real image.
- Same-pass ControlNet + quantized LoRA produced full-frame checker/noise.
- Disabling quantized LoRA stopped the checker/noise, but also removed the
  LoRA effect.
- The compatibility shim in `nunchaku_compat.py` tried to keep packed low-rank
  tensors inside the existing rank slot by truncating wider tensors:

```python
return tensor[:, :target_rank].contiguous()
```

That is invalid for packed Nunchaku low-rank tensors. The packed layout
interleaves rank fragments, so slicing after packing can corrupt the base
low-rank branch. This explains why the output looked like structured
checker/noise instead of a normal bad image.

Backend attempt:

- Patched both:
  - `/home/nymph/NymphsModules/zimage/nunchaku_compat.py`
  - `/home/nymph/Z-Image/nunchaku_compat.py`
- Smaller tensors are still padded into the existing slot.
- Larger packed tensors are no longer truncated; they are passed through so the
  backend uses the real expanded packed LoRA tensor.
- Same-pass ControlNet + LoRA was restored as the intended product path after
  the Z-Image `0.1.114` packed-LoRA compatibility fix. If checker/noise appears
  again, first confirm the test WSL has both Nymphs Image `0.1.114+` and Nymphs
  Sprite `1.2.34+` installed.

Current Sprite behavior after the 2026-06-15 cleanup:

- `--controlnet-lora-mode` defaults to `on`.
- `on` means Pose Lab ControlNet and selected LoRA run in the same
  `controlnet_edit` request.
- `staged` remains available only for backend regression isolation.
- `off` remains a no-LoRA diagnostic path.

Live dev WSL validation:

```text
command:
generate-nymphscore ... --max-directions 1 --controlnet-lora-mode on

backend:
runtime=nunchaku
mode=controlnet_edit
lora=True
quantized_apply.updated_lora_modules=136

result:
/home/nymph/NymphsData/outputs/nymphs-sprite/goblin_scout/front_raw.png
```

That installed-runtime result is now treated as stale/mismatched-runtime
evidence, not the current product stance. Normal generation should stay
same-pass unless a fresh test on Nymphs Image `0.1.114+` and Nymphs Sprite
`1.2.34+` proves otherwise.

Next backend/frontend work:

1. Tune Pose Lab control strength and prompt language for stronger pose
   following in same-pass mode.
2. Compare `guide_strength` values and `controlnet_guidance_scale` with
   one-direction tests before running 8/16 directions.
3. Keep the temporary ControlNet PNGs as diagnostics, but the real editable
   source of truth remains Pose Lab JSON.
4. Package the Z-Image backend fix so test WSL installs get the updated
   `nunchaku_compat.py`.

## Patch Checkpoint: 2026-06-12 Pose Following Defaults

After the staged fallback, Pose Lab was tested as a separate issue.

Finding:

- Pose Lab PNG rendering is valid.
- Z-Image ControlNet follows a clean OpenPose-style ref when the ref is
  visually strong.
- Same-pass ControlNet + mks0813 LoRA also follows the ref after the packed
  LoRA truncation bug was fixed.
- The weak/ignored-pose behavior was mainly a defaults problem, especially
  using high text CFG guidance during ControlNet generation.

Reference note:

- The local Diffusers `ZImageControlNetPipeline` example for Z-Image Turbo
  ControlNet uses `guidance_scale=0.0`.
- The Z-Image Turbo ControlNet Union 2.1 model card recommends control strength
  in the `0.65-1.00` range.

Implemented defaults:

- `--controlnet-guidance-scale` now defaults to `0.0`.
- `guide_strength_scale()` now maps:

```text
soft   -> 0.75
normal -> 0.90
strong -> 1.00
```

Validation run:

1. Created a temporary diagnostic Pose Lab set with raised left arm and wide
   legs.
2. Ran one direction with `--debug-no-lora`, strong ref, CFG `0.0`.
3. Output followed the pose.
4. Ran one direction with mks0813 LoRA enabled using normal defaults.
5. Output still followed the raised-arm/wide-stance pose and passed mechanical
   gates.
6. Removed the temporary diagnostic pose set afterward.

Current stance:

- If the output is clean but pose still feels soft, first try `Ref Strength:
  Strong`.
- Keep ControlNet guidance/CFG at `0.0` by default for Pose Lab runs.
- Prompt text should describe identity, not visual style or limb placement.
  LoRA owns style. Pose Lab owns limb placement.

## Patch Checkpoint: 2026-06-15 Prompt Ownership Cleanup

Problem:

- Raw ControlNet + LoRA output still looked far worse than expected.
- Postprocess could be disabled, but the request still carried inherited
  Foundry style language: `pixel art`, `sprite`, `HD-2D`, green-screen,
  `48px`, photorealistic/3D-render negatives, and direction text that could
  fight Pose Lab.

Implemented:

- `pipeline/foundry_gen_nymphscore.py` now cleans every generation payload at
  runtime, including prompt presets and typed prompts.
- Style clauses are stripped before sending to Z-Image.
- Pose clauses are stripped when Pose Lab ControlNet refs are active.
- ControlNet runs no longer append text direction prompts; the Pose Lab PNG is
  the direction/pose authority.
- Positive prompt shape is now:

```text
LoRA trigger
cleaned character identity
single full body / isolated figure / no background / no shadow constraints
Pose Lab control instruction, only when ControlNet is active
```

- Negative prompt shape is now:

```text
cleaned mechanical negatives
no multiple characters
no text/watermark/frame
no scenery/background/floor/ground plane
no cast/drop/contact shadow
Pose mismatch negatives, only when ControlNet is active
```

- UI defaults now match the backend defaults:

```text
width=1024
height=1024
steps=9
lora_scale=0.85
```

Next test:

1. Update/install Nymphs Sprite `1.2.37+` on the test WSL.
2. Disable Sprite postprocess for the first check.
3. Run one or two directions with mks0813 and Pose Lab refs.
4. Inspect raw outputs first. Do not judge the Python pixel/cutout stage until
   the raw Z-Image + LoRA + ControlNet result looks like the expected model
   quality.
