# Nymphs Sprite Distillation Plan

Current as of 2026-06-09.

## North Star

Nymphs Sprite should be a slick, reliable sprite-set generator for games. The
old Sprite Foundry codebase is the reference implementation, but the new module
should not feel like a research workbench full of competing flows.

The user-facing flow is:

```text
Character -> Guide -> Style -> Generate -> Review -> Export
```

The local `/home/nymph/NymphsModules/sprite-foundry` checkout can stay as an
archive/reference. The active product repo is:

```text
/home/nymph/NymphsModules/nymphs-sprite
https://github.com/nymphnerds/nymphs-sprite
```

The module name is **Nymphs Sprite**.

## Current State

- `nymphs-sprite` has been wiped and rebuilt from the more evolved
  `sprite-foundry` module.
- The manifest identity is now `id: nymphs-sprite`, `name: Nymphs Sprite`.
- Runtime defaults use port `8098`.
- Data defaults use `$HOME/NymphsData/*/nymphs-sprite`.
- The UI keeps the Sprite Foundry look and feel but is now organized as:
  Runtime, Character, Guide, Style, Generate, Review, Advanced.
- The Guide panel currently exposes body type and guide strength as UI intent.
- The inherited lifecycle buttons still exist under Advanced so nothing useful
  is lost while the flow is being distilled.

## Output Ownership Rule

Nymphs Image / Z-Image is the backend engine only. Nymphs Sprite owns all sprite
workflow artifacts.

Generated sprites, guide sheets, temporary backend handoff files, review
artifacts, accepted sets, and exports should stay under Nymphs Sprite-owned
paths:

```text
$HOME/NymphsData/outputs/nymphs-sprite/
$HOME/NymphsData/tmp/nymphs-sprite/
$HOME/NymphsData/config/nymphs-sprite/
$HOME/NymphsData/logs/nymphs-sprite/
```

Do not let a Nymphs Sprite generation silently dump final assets into generic
Nymphs Image / Z-Image output folders. Passing an explicit `output_dir` to the
backend is the correct pattern.

## What We Keep From Sprite Foundry

Keep these ideas:

- 8-direction sprite-set target.
- Per-direction review and accept/reject thinking.
- Contact sheets and preview strips.
- Deterministic export packs with manifests.
- Normal/depth map ambitions for Godot/game lighting.
- Godot packaging/export interest.
- Lifecycle metadata where it helps debugging and reproducibility.
- Strong prompt presets as test fixtures.

Avoid exposing these as the main workflow:

- Multiple confusing generation methods as top-level choices.
- Run IDs and attempt IDs in the normal path.
- Foundry internals as first-screen controls.
- Backend details as the product concept.

## Generation Methods Clarified

### NymphsCore / Z-Image

This is the main path for Nymphs Sprite.

Today, this path uses Z-Image/Nunchaku/LoRA for generation. In the copied code it
does not yet truly pass per-direction ControlNet guide images into Z-Image. The
new work should wire that in.

### Stack A v2

Original ComfyUI/JuggernautXL + pixel-art LoRA path. Useful as historical
reference and comparison material, but not the core Nymphs Sprite runtime.

### Morph ControlNet

Original ComfyUI path using body-class depth/canny style control. The concept is
very important: body classes and guides can stabilize silhouette and direction.
The exact implementation is legacy.

### Turnaround Sheet

Original CharTurn-style multi-view sheet idea. Useful for identity research, but
not the first clean path. We decided to prefer ControlNet refs over chasing a
Z-Image CharTurn LoRA.

## ControlNet Mental Model

ControlNet does not create the body guide. Nymphs Sprite creates or receives the
guide first, then Z-Image uses that guide as visual conditioning.

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
- MLSD: mostly for hard-surface structures, not a primary character path.
- Gray: research-only until tested.

User-facing language should be:

- Direction Guides
- Pose Guide
- Sketch Guide
- Outline Guide
- Body Guide

Avoid leading with internal words like preprocessor, control map, or union model.

## The Pose / Guide Panel

This is the big idea.

The Guide panel should eventually let the user make or adjust the ControlNet
refs used for generation. The simple version comes first:

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
- regenerating one bad direction with a corrected guide
- deriving a guide from an auditioned/generated image

## Best Working Flow To Build First

Build and test from the top down:

1. Character
   - Pick a preset or write a prompt.
   - Keep subject ID, prompt, negative prompt.

2. Guide
   - Pick body type.
   - Generate deterministic 8-direction guide refs.
   - Show a guide contact sheet.

3. Style
   - Pick LoRA.
   - Pick sprite size and palette options.

4. Generate
   - Generate all 8 directions through Z-Image.
   - Use the body/direction guides as ControlNet refs.
   - Save into Nymphs Sprite output folders, not generic Z-Image output.

5. Review
   - Use the preview strip/audition UX from Nymphs Image as inspiration.
   - Select winners.
   - Reject bad directions.
   - Regenerate selected directions.

6. Export
   - Export a clean game-ready pack.
   - Preserve interest in Godot packaging.
   - Keep normal/depth maps as a future export layer.

## Audition / Regenerate Stage

The audition stage should be simple:

- generate candidates
- inspect in preview strip
- select winner per direction
- regenerate only failed directions
- export accepted set

Future advanced loop:

```text
bad direction -> make/edit guide -> regenerate that direction -> accept winner
```

This is where the pose panel becomes powerful. A failed sprite can become the
starting point for a manual pose/outline ref.

## Godot / Packaging

Godot export remains interesting and should not be discarded.

Target export ideas:

- standard PNG direction set
- contact sheet
- manifest JSON
- optional normal maps
- optional depth maps
- Godot-ready import folder/package
- checksums/provenance for reproducibility

Do not block the first generator MVP on Godot packaging. Make the sprite set
work first, then package it cleanly.

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

### Slice 1: UI Sanity

- Nymphs Sprite appears, Sprite Foundry does not.
- UI opens at `http://127.0.0.1:8098/nymph`.
- Sidebar shows Character, Guide, Style, Generate, Review.
- Advanced keeps inherited lifecycle tools.

### Slice 2: Current Z-Image Path

- Start backend.
- Confirm LoRA list loads.
- Generate one 8-way set without ControlNet refs.
- Confirm outputs land under `$HOME/NymphsData/outputs/nymphs-sprite`.

### Slice 3: Guide Preview

- Choose each body type.
- Generate guide contact sheet.
- Confirm guide files are deterministic and visible.

### Slice 4: ControlNet Wiring

- Send one guide into Z-Image ControlNet.
- Compare no-guide vs guide output.
- Confirm the guide meaningfully affects pose/shape.

### Slice 5: 8-Direction Control

- Generate all 8 directions with guides.
- Verify direction read, consistency, and silhouette.
- Record best settings for guide strength.

### Slice 6: Audition

- Generate multiple candidates for one direction.
- Select a winner in the strip.
- Regenerate a rejected direction.

### Slice 7: Export

- Export accepted set.
- Verify manifest, filenames, dimensions, and game import shape.

## Immediate Implementation Order

1. Finish the Nymphs Sprite repo transplant.
2. Remove old Sprite Foundry from registries so it no longer appears.
3. Keep the current distilled UI and test it in the test WSL.
4. Implement actual guide preview generation.
5. Wire one guide image into Z-Image ControlNet.
6. Expand to 8-direction guided generation.
7. Add audition/regenerate UX using a Nymphs Image-style preview strip.
8. Revisit Godot/depth/normal export once albedo sets are reliable.

## Environment Notes

- Dev WSL: this workspace.
- Test WSL name: `NymphsCore`.
- Test WSL is the normal end-user path for Manager install/update testing.
- Do not manually mutate installed test module state unless explicitly approved.
- Publish/update registry/install through Manager for real test validation.

## Working Principle

Nymphs Sprite should feel like directing a sprite sheet, not configuring an AI
pipeline.
