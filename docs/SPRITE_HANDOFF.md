# Nymphs Sprite Handoff

Last updated: 2026-06-05

## Goal

Build `nymphs-sprite` as the NymphsCore module version of Sprite Foundry:

```text
Sprite Foundry flow
  -> Nymphs Manager UI
  -> Nymphs Image / Z-Image generation
  -> Foundry-style review, gates, maps, and export
```

Do not make ComfyUI a runtime dependency. The original ComfyUI graphs are a
parity map only.

## Current Published State

`nymphs-sprite` is published to the dev registry at `0.1.17`.

Raw manifest:

```text
https://raw.githubusercontent.com/nymphnerds/nymphs-sprite/main/nymph.json
```

Raw manifest hash:

```text
375ec6ff17ad5feb726276946cedd6d174ba713f12713591cafc7de99ee0c1c8
```

Latest module commit when this handoff was written:

```text
4dbce59 Fix Sprite roster presets and shared model cache
```

Dev registry commit:

```text
9e86936 Update dev registry for nymphs-sprite 0.1.17
```

## Repos

```text
NymphsModules/nymphs-sprite
  Manager-facing Nymph module, fetch actions, sprite UI, post-process runner.

NymphsModules/sprite-foundry
  Nymphs fork of upstream Sprite Foundry. Keeps Foundry DB, run/attempt model,
  gates, review concepts, map/finish/export commands, and adds
  foundry generate-nymphscore.

NymphsModules/zimage
  Nymphs Image backend. Owns Z-Image Turbo runtime, Nunchaku, LoRA loading,
  backend model fetch, and the shared Hugging Face cache.
```

## Model And Data Boundaries

Do not create new model directories for Sprite.

Shared Hugging Face model cache:

```text
$HOME/NymphsData/cache/huggingface
$HOME/NymphsData/cache/huggingface-home
```

Shared Z-Image generation preset:

```text
$HOME/NymphsData/config/zimage/generation-preset.env
```

Sprite LoRA library:

```text
$HOME/LoRA/loras/nymphs-sprite
```

Sprite module config/output/log roots:

```text
$HOME/NymphsData/config/nymphs-sprite
$HOME/NymphsData/outputs/nymphs-sprite
$HOME/NymphsData/logs/nymphs-sprite
```

`Model Fetch -> Complete Sprite Stack` fetches:

```text
Z-Image INT4 r32 backend through Nymphs Image's fetcher
mks0813 pixel-art LoRA
tarn59 pixel-art LoRA
ControlNet Union asset into shared HF cache
Depth Anything V2 Small asset into shared HF cache
```

Complete fetch leaves `tarn59_pixel_art` selected. Keep it that way: it passed
a one-direction smoke test. `mks0813_pixel_art` is retained as an alternate but
currently fails Nunchaku LoRA composition with a tensor-shape mismatch.

Selected LoRA config:

```text
$HOME/NymphsData/config/nymphs-sprite/selected_lora.env
```

## Preset State

The Manager preset dropdown is roster-pure:

```text
profiles/foundry_export_roster.json       original 92 production export packs
profiles/foundry_character_presets.json   same 92 entries, enriched where configs exist
```

Current counts:

```text
92 roster entries total
51 generation-ready entries with local prompt/source configs
41 roster-only entries disabled until configs are imported or reconstructed
0 extra h3d/local/duplicate entries
0 "Foundry Character" labels
```

Do not add non-roster configs to the visible dropdown. If a local config is not
in the original roster, it belongs in research/debug notes, not the production
preset surface.

## What Works Now

The current usable module flow is:

```text
install/update from dev registry
  -> Model Fetch / Complete Sprite Stack
  -> open Nymphs Sprite UI
  -> select generation-ready roster preset
  -> select LoRA
  -> Generate Sources
  -> preview/pick source images
  -> Generate + Process
```

Implemented pieces:

- Nymphs Image-style Manager UI.
- Roster preset dropdown.
- LoRA selection from downloaded Sprite LoRAs.
- Fast source generation path through Z-Image `/generate`.
- Module-action fallback for WebView/CORS cases.
- Fast `/server_info` probe before direct `/generate`.
- Module bridge auto-starts Z-Image when offline.
- Foundry-style Python post-process:
  - copy raw source images
  - background/green-screen cleanup
  - foreground crop
  - square pad
  - nearest-neighbor resize
  - transparent albedo PNG
  - previews/contact sheet
  - `sprite_batch.json`
  - basic mechanical checks
- Foundry bridge action:
  - `foundry_generate`
  - wraps `python3 -m foundry.cli generate-nymphscore`
  - uses selected imported preset `source_config`

Current output roots:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject-id>/<batch-id>
NymphsModules/sprite-foundry/bakeoff/<run_id>
```

## What Is Not Full Flow Yet

The original Sprite Foundry full flow is not complete in Manager yet.

Missing Manager-visible lifecycle pieces:

- `review-show`
- raw/pixel accept
- raw/pixel reject
- regen loop
- produce depth/normal/finish artifacts
- finish board
- deterministic export
- export manifest/checksum surfacing
- Foundry run browser/status board in the Sprite UI

Missing backend parity:

- Real Z-Image ControlNet/morphology conditioning is not proven.
- Depth Anything is fetched/staged but not wired as a full per-direction map
  stage in the module.
- Normal maps are not proven.
- Godot finish-lab parity is not wired.

## ControlNet Reality

Sprite Foundry used ComfyUI ControlNet/depth/canny paths to lock morphology,
especially for monster and non-humanoid lanes.

Current Nymphs reality:

```text
Z-Image/Nunchaku generation works.
Z-Image Turbo LoRA loading works with tarn59.
Z-Image ControlNet assets can be fetched.
No working Z-Image ControlNet pipeline path has been proven in the current
Nymphs Image runtime.
```

Do not promise ControlNet parity, GLB, game-mesh, or full Foundry export parity
until those paths are proven.

Likely short-term replacement strategy:

```text
generate albedo/source first
  -> derive depth with Depth Anything
  -> derive normals from depth
  -> use post-process / Qwen-edit-style refinement where needed
  -> revisit ControlNet if Nunchaku or diffusers exposes a usable Z-Image path
```

## Full Target Flow

The target Manager flow should become:

```text
select original Foundry roster preset
  -> select backend and LoRA
  -> generate 8 source directions
  -> inspect raw/pixel contact sheets
  -> accept/reject/regen attempts
  -> produce depth and normal maps
  -> inspect finish board
  -> export deterministic Foundry pack
```

Target filesystem/export contract:

```text
bakeoff/<run_id>/
  raw images
  pixel sprites
  contact sheets
  recipe.json
  manifest.json

exports/<subject_slug>/<run_id>/
  albedo/
  normal/
  depth/
  preview/
  manifest.json
  checksums
```

## Next Build Steps

1. Test `0.1.17` from the dev registry in the managed/test WSL.
   - Update through Manager only.
   - Do not manually sync installed files.
   - Run `Model Fetch -> Complete Sprite Stack`.
   - Confirm status shows shared HF cache and `selected_lora_candidate=tarn59_pixel_art`.
   - Generate one enabled preset, preferably `Goblin Scout`.

2. Promote Foundry lifecycle actions into `nymphs-sprite`.
   - Add scripts/actions for:
     - `foundry_review_show`
     - `foundry_accept`
     - `foundry_reject`
     - `foundry_regen`
     - `foundry_produce`
     - `foundry_export`
   - Keep the Foundry DB and lifecycle logic inside `sprite-foundry`.
   - Keep the Sprite UI as the Manager workbench.

3. Add a Foundry run browser to `ui/manager.html`.
   - Show latest run id, subject, state, gate result, attempt count.
   - Show raw/pixel/contact-sheet artifacts.
   - Expose accept/reject/regen/produce/export commands.

4. Wire map production carefully.
   - Validate `foundry_maps.py` after the `sprite_target` changes.
   - Confirm depth outputs are generated at the selected sprite size.
   - Add normal derivation only after depth is stable.

5. Revisit morphology/control.
   - Audit current Nymphs Image, Nunchaku, and diffusers APIs.
   - If no Z-Image ControlNet path exists, document the two-pass fallback and
     keep ControlNet assets staged but not advertised as working.

6. Reconstruct the 41 missing roster configs.
   - Keep them original-roster only.
   - Do not pollute the dropdown with local debug configs.
   - Mark entries generation-ready only when a prompt/source config exists.

## Test Commands

Static checks:

```bash
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/nymph.json
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/profiles/foundry_character_presets.json
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.sh
python3 -m py_compile /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.py
bash /home/nymph/NymphsModules/sprite-foundry/verify.sh
```

Preset sanity:

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/home/nymph/NymphsModules/nymphs-sprite/profiles/foundry_character_presets.json')
d = json.loads(p.read_text())
items = d['presets']
print('total', len(items))
print('ready', sum(1 for x in items if x.get('generation_ready')))
print('foundry_labels', sum('Foundry Character' in x.get('label', '') for x in items))
print('h3d', sum(x['id'].startswith('h3d_') for x in items))
PY
```

Expected:

```text
total 92
ready 51
foundry_labels 0
h3d 0
```

## Rules To Preserve

- Source work happens in the dev/source checkout.
- Test WSL is for end-user testing only.
- Do not manually edit installed module files, markers, cached manifests, or
  runtime state.
- Publish module first, verify raw `nymph.json`, then update registry.
- Never advertise a version that is not pushed and raw-available.
- Module install/update scripts own installed `nymph.json` and
  `.nymph-module-version`.
- Keep fetched models out of git.
- Keep shared backend models in the shared Nymphs cache.
- Keep Sprite LoRAs in the shared LoRA library.
- Do not add ComfyUI as a dependency.
