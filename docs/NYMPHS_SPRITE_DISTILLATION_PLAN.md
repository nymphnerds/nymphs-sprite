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
Nymphs Sprite 1.2.21
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
- Pick sprite size and palette options.
- Keep advanced model/rank/seed/step controls available but not dominant.

### 4. Generate

- Generate all selected directions through Z-Image.
- Use Pose Lab body/direction guides as ControlNet refs.
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

1. Test/update installed Nymphs Sprite `1.2.21` or newer in the `NymphsCore`
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
version=1.2.21 or newer
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

- Nymphs Sprite `1.2.21`
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

1. Update/install Nymphs Sprite `1.2.21+` on the `NymphsCore` test WSL.
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
  `controlnet_guidance_scale: 1.0`.
- Record `controlnet_guidance_scale` in `recipe.json`.

Next validation:

1. Update the test WSL to Nymphs Sprite `1.2.22`.
2. Start Z-Image fresh if the backend gets wedged after a failed run.
3. Run the same 8-way Goblin Scout set.
4. Confirm the new `recipe.json` uses the selected mks0813 LoRA path and
   `lora_trigger: pxlstl`.
5. Confirm `controlnet_directions` contains all generated directions.
6. Confirm `controlnet_guidance_scale` is `1.0`.
7. If outputs are still unresolved noise, isolate with a no-LoRA direct
   `controlnet_edit` probe before blaming Pose Lab. If no-LoRA also produces
   noise, investigate the Z-Image ControlNet runtime/adaptation. If no-LoRA
   works, investigate LoRA + ControlNet interaction and scale.
- A working 8-direction generator matters more than preserving every old
  Foundry feature.
