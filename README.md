## Nymphs Sprite

Nymphs Sprite is a NymphsCore module for making game-ready sprite sets with a
clean, guided workflow:

```text
Character -> Guide -> Style -> Generate -> Review -> Export
```

This repo replaces the old stale Nymphs Sprite codebase with the more evolved
Sprite Foundry module as a starting point. The goal is not to preserve every
experimental branch from Foundry. The goal is to distill the best ideas into a
slick, reliable sprite factory for NymphsCore.

<p align="center">
  <img src="ui/nymphs_preview_forest.png" alt="Nymphs Sprite preview" width="680">
</p>

## What It Does

Nymphs Sprite generates directional sprite attempts through the local Nymphs
Image / Z-Image backend, keeps review state for each direction, and exports
accepted results as structured game assets.

The first working target is a dependable 8-direction flow:

- Define a character prompt, subject id, sprite size, seed, LoRA, and style.
- Generate one attempt per direction with the Nymphs Image backend.
- Review results by direction.
- Regenerate weak directions without throwing away the whole set.
- Export accepted sprites from this module's own output folders.

The next major upgrade is a ControlNet guide panel: simple body guides, pose
refs, and eventually hand-editable stick/sketch poses that make direction and
pose control much less random.

## Module Boundaries

Nymphs Sprite uses Nymphs Image as a backend, but owns its outputs.

Default paths:

```text
$HOME/Nymphs-Sprite
$HOME/NymphsData/outputs/nymphs-sprite
$HOME/NymphsData/config/nymphs-sprite
$HOME/NymphsData/logs/nymphs-sprite
$HOME/NymphsData/cache/huggingface
$HOME/LoRA/loras
```

That means your existing Hugging Face model cache and LoRA downloads are shared
with Nymphs Image, while generated sprite runs stay under
`NymphsData/outputs/nymphs-sprite`.

## Current Backend

The current primary generation path is:

```text
Nymphs Sprite UI
  -> local module server
  -> Nymphs Image / Z-Image API
  -> Z-Image Turbo / Nunchaku
  -> optional Z-Image pixel-art LoRA
  -> Nymphs Sprite run output
```

ControlNet support is staged. The UI already has the start of a Guide section,
but the current Z-Image path does not yet pass per-direction ControlNet images
into generation. That is the next practical milestone after basic install and
generation testing.

## Distilled UI Flow

### Character

Choose or write the character prompt, subject id, and negative prompt.

### Guide

Choose the body/pose guide strategy. Today this is mostly a planning surface.
Soon it should generate previewable ControlNet reference sheets for each
direction.

### Style

Pick the model, LoRA, trigger, scale, dimensions, steps, and seed.

### Generate

Create a full directional run. The default target is 8 directions:

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

16-direction support is planned once 8-direction quality is dependable.

### Review

Inspect attempts, accept strong directions, reject weak directions, and
regenerate only what needs another pass.

### Export

Package the accepted set for downstream game engines. Godot-friendly packaging,
depth maps, and normal maps are planned as part of the production export path.

## What We Kept From Sprite Foundry

Sprite Foundry had a lot of useful machinery mixed with a lot of experimental
surface area. The pieces worth carrying forward are:

- Directional run organization.
- Per-direction review and rejection.
- Regeneration/audition loops.
- Export manifests and deterministic asset folders.
- Future depth/normal/Godot verification ideas.
- The dark Nymphs-style UI shell, tightened into a simpler flow.

The pieces to demote or hide are:

- Too many generation modes on the first screen.
- Legacy ComfyUI-first assumptions.
- Confusing lifecycle buttons before a user has generated anything.
- Experimental flows that are useful as reference but not part of the everyday
  path.

## Install

Install through the NymphsCore Manager dev registry once this module is visible
as `Nymphs Sprite`.

For local development:

```bash
git clone https://github.com/nymphnerds/nymphs-sprite.git
cd nymphs-sprite
bash -n scripts/*.sh
python3 -m py_compile pipeline/foundry_gen_nymphscore.py scripts/sprite_foundry_ui_server.py
```

The module manifest starts the UI on port `8098`.

## First Test Pass

After install, test from top to bottom:

1. Confirm Manager shows `Nymphs Sprite`, not `Sprite Foundry`.
2. Open the UI and confirm the sidebar reads `Character -> Guide -> Style -> Generate -> Review`.
3. Confirm status reports the shared Hugging Face cache and local LoRAs.
4. Generate a tiny 8-direction run at conservative settings.
5. Confirm outputs land under `NymphsData/outputs/nymphs-sprite`.
6. Review one direction and try a reject/regenerate loop.
7. Export only after accepted images exist.

## Roadmap

Near-term:

- Wire guide preview generation to actual saved guide sheets.
- Pass per-direction ControlNet refs into the Z-Image backend.
- Add a compact audition strip inspired by Nymphs Image.
- Make review/regenerate the main workflow instead of an advanced lifecycle
  panel.

Next:

- Pose panel for stick/sketch/body guide editing.
- 16-direction option.
- Godot-ready export packaging.
- Normal and depth post-process outputs.
- Stronger sprite manifest contract for game projects.

The living design note is in
[docs/NYMPHS_SPRITE_DISTILLATION_PLAN.md](docs/NYMPHS_SPRITE_DISTILLATION_PLAN.md).

## License

[MIT](LICENSE)

Nymphs Sprite builds from the original Sprite Foundry foundation by MCP Tool
Shop, released under MIT.
