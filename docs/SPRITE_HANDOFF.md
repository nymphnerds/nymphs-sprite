# Nymphs Sprite Handoff

Last updated: 2026-06-06

## Goal

Build `nymphs-sprite` as the NymphsCore module version of Sprite Foundry:

```text
original Sprite Foundry production flow
  -> Nymphs Manager UI
  -> Nymphs Image / Z-Image / Nunchaku backends
  -> Foundry-style review, gates, maps, and export
```

Do not make ComfyUI or SDXL a runtime dependency. The upstream Sprite Foundry
ComfyUI graphs are reference material only.

This module is a 2D sprite production module. It does not create meshes. Mesh,
splat, GLB, or game-mesh conversion belongs in TripoSplat/Pixal3D/TRELLIS or a
later dedicated conversion module.

## Session Checkpoint

Current source version target:

```text
nymphs-sprite 0.1.38
```

Latest pushed source state from 2026-06-06:

- Nunchaku fork ControlNet fix pushed:
  `b092d6904f6ace0cc6fa65f3ac0beb1cf257ac40`.
- Nymphs Image/Z-Image `0.1.105` pushed and registry-updated; raw manifest was
  verified before registry update.
- Nymphs Sprite `0.1.35` pushed with the user-facing UI baseline:
  standard `local_url` UI, same-origin output browser, hidden Foundry-facing
  controls, and Nymphs Image-style output strip management.
- `0.1.36` is a docs/handoff refresh so the next session starts from the actual
  pushed state instead of the older `0.1.33` transition notes.
- `0.1.37` makes Open Outputs visible as a first-class Runtime control, renames
  the Z-Image launcher, and keeps the strip folder menu matched to Nymphs Image:
  Choose Folder, Move Selected, Delete Folder.
- `0.1.38` moves Open Outputs onto its own full-width Runtime row so the
  sidebar does not crowd four text buttons into one line.

Current tested dev sanity state:

- `Generate Sources` and ControlNet-guided direction generation have both run
  successfully in dev WSL through shared Nymphs Image/Z-Image/Nunchaku.
- The generated Sprite ControlNet smoke output was written under the shared
  Z-Image output root and then surfaced in the Sprite strip.
- The Sprite UI now follows the standard generation-module contract:
  `local_url`, `/nymph`, `/health`, `/server_info`, `/api/outputs`, `/outputs`,
  and normal `/ui` assets.
- The forest background is served as `/ui/nymphs_preview_forest.png`, matching
  the Nymphs Image pattern. Do not return to embedded `local_html` data URIs.
- The visible `Foundry Run` button and visible `Foundry Status` Manager action
  are removed. The underlying Foundry scripts remain available as developer
  reference/parity tools, not as the normal user workflow.
- The Sprite UI has two different "open" actions now:
  `Z-Image` starts/opens the shared Nymphs Image backend, while `Open Outputs`
  opens the generated output folder. Do not bury Open Outputs in the strip
  folder menu.

Registry note:

- `nymphs-sprite` is still not listed in
  `/home/nymph/NymphsModules/nymphs-registry/nymphs.json`.
- Do not bump the registry for Sprite unless it is added to the catalog or an
  existing catalog entry must advertise a new remote manifest.
- For any future registry change: push Sprite first, verify raw GitHub
  `nymph.json`, then update/push registry.

Raw manifest to verify after push:

```text
https://raw.githubusercontent.com/nymphnerds/nymphs-sprite/main/nymph.json
```

Manager/test install must happen through normal module install/update flows.
Do not manually copy source files into the test/runtime WSL.

## Important Repos

```text
/home/nymph/NymphsModules/nymphs-sprite
  Manager-facing Nymph module, fetch actions, sprite UI, post-process runner.

/home/nymph/NymphsModules/sprite-foundry
  Nymphs fork of Sprite Foundry. Keeps Foundry DB, run/attempt lifecycle,
  gates, review concepts, map/finish/export commands, and generate-nymphscore.

/home/nymph/NymphsModules/zimage
  Nymphs Image backend source. Owns Z-Image Turbo runtime, Nunchaku integration,
  model fetch, LoRA loading, and the shared Hugging Face cache.

/home/nymph/Z-Image
  Installed/dev runtime checkout for Nymphs Image in this WSL. It may be older
  than source. Update it through the module update action, not by hand.

/home/nymph/nunchaku
  Local Nunchaku fork checkout. Relevant to Z-Image LoRA and future ControlNet
  backend work.
```

## Current Source Summary

The Sprite repo is expected to be clean after `0.1.38` is pushed. The current
module baseline is:

```text
CHANGELOG.md
docs/SPRITE_HANDOFF.md
nymph.json
scripts/nymphs_sprite_generate_directions.py
scripts/nymphs_sprite_ui_server.py
ui/manager.html
```

No untracked `__pycache__` artifacts should be left after static checks.

High-level state now:

- Adds/normalizes three Z-Image Turbo pixel-art LoRAs.
- Moves Sprite LoRAs to the shared LoRA module layout.
- Stops using a private legacy Sprite LoRA subdirectory.
- Resolves stale selected-LoRA paths back to shared canonical paths.
- Makes Sprite status expose the selected Nymphs Image/Z-Image rank and
  precision.
- Makes Sprite UI/module generation call "load selected Z-Image model first"
  using the same pattern as Nymphs Image.
- Removes the fallback that silently avoided `mks0813_pixel_art`.
- Uses selected source images as Z-Image/Nunchaku `controlnet_edit` guidance
  for `Generate + Process`.
- Keeps Depth Anything staged/fetchable, but depth/normal map production is not
  wired as a finished output stage yet.
- Keeps source generation on module-owned scripts that call the shared Z-Image
  API, while the Sprite UI itself is served through the standard local
  `http://127.0.0.1:8098/nymph` route.
- Keeps the actual generation method copied from Nymphs Image at the API
  contract level: `/api/model/load` then `/generate`, same model/rank/LoRA
  payload fields, same shared runtime.
- Serves Sprite's output browser directly from its local UI server with
  `/api/outputs` and `/outputs/<source>/...` URLs.
- Copies the Nymphs Image strip management model: select, select all, clear
  selection, move selected, delete selected, and delete top-level managed
  folders.

## Shared Model And Data Contract

Do not create new model roots for Sprite.

Shared Hugging Face cache:

```text
$HOME/NymphsData/cache/huggingface
$HOME/NymphsData/cache/huggingface-home
```

Shared Z-Image generation preset:

```text
$HOME/NymphsData/config/zimage/generation-preset.env
```

This file is owned by Nymphs Image. Sprite reads/mirrors it. Sprite should not
invent a separate model-rank source of truth.

Unified LoRA library:

```text
$HOME/LoRA/loras
$HOME/LoRA/loras/<lora-id>/<lora-id>.safetensors
```

This should match the LoRA module and be usable by:

- Nymphs Image
- Nymphs Sprite
- LoRA module
- Blender addon
- future remote UI

Sprite module config/output/log roots:

```text
$HOME/NymphsData/config/nymphs-sprite
$HOME/NymphsData/outputs/nymphs-sprite
$HOME/NymphsData/logs/nymphs-sprite
```

Selected Sprite LoRA config:

```text
$HOME/NymphsData/config/nymphs-sprite/selected_lora.env
```

## LoRA State

The intended visible LoRA choices are exactly:

```text
mks0813_pixel_art
skyasl_pixel_artist
tarn59_pixel_art
```

Current shared LoRA paths:

```text
$HOME/LoRA/loras/mks0813_pixel_art/mks0813_pixel_art.safetensors
$HOME/LoRA/loras/skyasl_pixel_artist/skyasl_pixel_artist.safetensors
$HOME/LoRA/loras/tarn59_pixel_art/tarn59_pixel_art.safetensors
```

LoRA source repos:

```text
mks0813_pixel_art
  repo: https://huggingface.co/mks0813/z-image-turbo-pixel-lora
  source file: epoch-1.safetensors
  trigger: pxlstl
  notes: best visual match so far; keep as default.

skyasl_pixel_artist
  repo: https://huggingface.co/SkyAsl/Pixel-artist-Z
  source file: adapter_model.safetensors
  trigger: a pixel art character
  notes: character-oriented backup.

tarn59_pixel_art
  repo: https://huggingface.co/tarn59/pixel_art_style_lora_z_image_turbo
  source file: pixel_art_style_z_image_turbo.safetensors
  trigger: Pixel art style.
  notes: backup style LoRA.
```

`scripts/nymphs_sprite_fetch_lora.sh` now normalizes public LoRA key formats
when writing to the shared LoRA library:

```text
base_model.model.     -> stripped
diffusion_model.      -> stripped
transformer.          -> stripped
.lora_A.default.weight -> .lora_A.weight
.lora_B.default.weight -> .lora_B.weight
```

It writes metadata such as:

```text
nymphs_source_repo
nymphs_source_filename
nymphs_zimage_lora_normalized
nymphs_lora_ranks
```

Important: existing local downloaded LoRAs can be normalized offline. The fetch
script first checks the shared library path, then normalizes in place if the
file already exists.

## mks / Rank Confusion Diagnosis

The mks LoRA is not inherently bad.

What happened:

1. Sprite initially used stale/private LoRA paths and only showed two choices.
2. Public LoRA key formats did not match the Nunchaku Z-Image mapper.
3. The installed `/home/nymph/Z-Image` runtime was older than source and did
   not resolve the selected Nunchaku rank file as safely as source does.
4. An error appeared:

```text
Trying to set a tensor of shape torch.Size([3840, 32])
in "qkv_proj_down" (which has shape torch.Size([3840, 128]))
```

That looked like "mks is rank-bad", but direct isolation showed the cleaner
truth:

- Exact local `svdq-int4_r32-z-image-turbo.safetensors` loads with rank-32
  tensors.
- Applying normalized `mks0813_pixel_art` to the exact local r32 transformer
  succeeds.
- After LoRA merge, fused QKV internals can show width 128. That is expected
  packed/internal low-rank behavior, not proof that r128 was selected.

Direct test result from the session:

```text
base_quantized_modules: 136
quantized_module_matches: 136
fused_qkv_matches: 34
fused_swiglu_matches: 34
unmatched_prefix_count: 0
quantized_apply.updated_lora_modules: 136
```

Conclusion:

```text
r32 + normalized mks works when the exact local r32 Nunchaku weight is loaded.
Do not switch the Sprite default to r128 just to hide the earlier mismatch.
All ranks should work as model choices, but the running Z-Image process and the
Sprite request must agree on the same selected rank/precision.
```

## Nymphs Image Model Loading Contract

Nymphs Image owns model selection. Sprite should copy that behavior.

Nymphs Image pattern:

```text
selected model/rank/precision
  -> POST /api/model/load
  -> if loaded: generate
  -> if restart scheduled: wait for /health
  -> POST /api/model/load again
  -> generate using same model/rank/precision
```

Sprite should follow that pattern through the module bridge:

- module bridge route in `scripts/nymphs_sprite_generate_directions.py`

Important: Sprite's Manager-facing UI should follow the same served UI family
as Nymphs Image and other generation modules: `local_url`, `/nymph`, cheap
`/health` and `/server_info`, and normal module-served `/ui` assets. Generation
still goes through the shared Z-Image API/runtime rather than a Sprite-owned
model backend.

Sprite status now forwards these values from `zimage_status.sh`:

```text
zimage_weight_profile_selected
zimage_weight_profile_ready
zimage_nunchaku_rank
zimage_nunchaku_precision
```

The Sprite UI builds Z-Image requests from those values instead of hardcoding
`int4 r32`.

Current dev status sample:

```text
zimage_weight_profile_selected=int4_r32
zimage_weight_profile_ready=true
zimage_nunchaku_rank=32
zimage_nunchaku_precision=int4
selected_lora_candidate=mks0813_pixel_art
selected_lora_path=/home/nymph/LoRA/loras/mks0813_pixel_art/mks0813_pixel_art.safetensors
downloaded_loras=mks0813_pixel_art,skyasl_pixel_artist,tarn59_pixel_art
```

## Runtime Caveat

Do not manually patch the installed/runtime WSL. Source fixes must move through
the normal module publish/update path.

Current backend state:

- Nunchaku fork has the Z-Image ControlNet RoPE packing fix pushed at
  `b092d6904f6ace0cc6fa65f3ac0beb1cf257ac40`.
- Nymphs Image/Z-Image source pins that Nunchaku commit in
  `scripts/_zimage_common.sh`.
- Z-Image `0.1.105` was pushed and its registry entry was updated after raw
  manifest verification.
- Sprite `Generate + Process` now sends selected source images to
  Z-Image `controlnet_edit` using `source-mode=controlnet` and a default
  `controlnet-scale=0.55`.

The dev sanity test proved the code path in dev WSL. The real acceptance test
still needs the user to update/install through Manager in the managed/test WSL
and generate from the published artifacts.

## Current Working Flow

Current intended module flow:

```text
install/update Nymphs Image
  -> install/update Nymphs Sprite
  -> Model Fetch / Complete Sprite Stack
  -> open Nymphs Sprite UI
  -> select original Foundry roster preset
  -> select LoRA
  -> Generate Sources
  -> preview/pick source images
  -> Generate + Process
  -> review/move/delete outputs from the strip
```

Implemented pieces:

- Nymphs Image-style Manager visual language.
- Original Foundry roster preset dropdown.
- Three shared LoRA choices.
- Fast source generation path through Sprite `generate_sources`, which calls
  shared Z-Image `/api/model/load` and `/generate` from the script side.
- Model-load-first behavior copied from Nymphs Image.
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
- ControlNet-guided direction generation:
  - selected strip images feed `Generate + Process`
  - Sprite sends those paths to Z-Image `controlnet_edit`
  - output metadata records `generation_mode`, `control_source_path`, and
    `controlnet_conditioning_scale`
- Output strip management:
  - Recent/date/folder browsing from Sprite's local `/api/outputs`
  - same-origin image URLs from `/outputs/<source>/...`
  - select current, select all, clear selection
  - move selected
  - delete selected images and matching metadata
  - delete top-level managed output folders

Developer-only Foundry bridge note:

- The repo still contains `foundry_generate` and `foundry_status` entrypoints.
- They are not shown in the main Sprite UI/Manager action row.
- Treat them as audit/parity tools only, not as the user workflow.

Current output roots:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject-id>/<batch-id>
$HOME/NymphsData/outputs/zimage
$HOME/Z-Image/outputs
$HOME/NymphsModules/zimage/outputs
```

## Preset State

The Manager preset dropdown should remain roster-pure:

```text
profiles/foundry_export_roster.json
profiles/foundry_character_presets.json
```

Current counts:

```text
92 roster entries total
51 generation-ready entries with local prompt/source configs
41 roster-only entries disabled until configs are imported or reconstructed
0 extra h3d/local/duplicate entries
0 "Foundry Character" labels
```

Do not add non-roster/debug configs to the visible dropdown. If a local config
is not in the original roster, keep it in research/debug notes only.

## Original Sprite Foundry Flow

The original Foundry flow is not "generate one image, then mesh." It is a 2D
production lifecycle:

```text
roster preset
  -> generate source directions
  -> review raw/pixel attempts
  -> accept/reject/regenerate
  -> produce sprite/map artifacts
  -> finish board
  -> deterministic export pack
```

The closest Nymphs target:

```text
select original Foundry roster preset
  -> select Z-Image model/LoRA
  -> generate 8 source directions
  -> inspect raw/pixel contact sheets
  -> accept/reject/regen attempts
  -> produce depth and normal maps
  -> inspect finish board
  -> export deterministic Foundry pack
```

Target export shape:

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

Current Nymphs Sprite batch shape:

```text
$HOME/NymphsData/outputs/nymphs-sprite/<subject-id>/<batch-id>/
  raw/                 original Z-Image outputs before sprite cleanup
  directions/          copied generated direction images, when source paths exist
  albedo/              cleaned transparent sprites; this is the useful sprite output
  preview/             contact sheets and raw inspection sheets
  sprite_batch.json    prompts, seeds, backend responses, provenance, checks
```

This is why the output folder currently contains several subfolders. It is
closer to a combined working/export bundle than original Foundry's final export
contract. Until normal/depth/finish parity exists, the UI should guide users to
the visible strip, the `Open Outputs` button, `albedo/`, and `preview/` rather
than making `raw/` and `directions/` feel like separate user workflows.

## What Is Not Full Flow Yet

Missing Manager-visible lifecycle pieces:

- `review-show`
- raw/pixel accept
- raw/pixel reject
- regen loop
- produce depth/normal/finish artifacts
- finish board
- deterministic export
- export manifest/checksum surfacing
- Foundry review/status board, if the developer parity path becomes useful
  again. Do not put Foundry Run back in the main user flow.

Missing backend parity:

- Z-Image/Nunchaku `controlnet_edit` works as a first guided path, but it is
  not yet full Sprite Foundry morphology parity.
- Depth Anything is fetched/staged but not wired as a full per-direction map
  production stage.
- Normal maps are not proven.
- Godot finish-lab parity is not wired.
- Mesh generation is intentionally out of scope for this module.

## ControlNet Reality

Sprite Foundry used ComfyUI ControlNet/depth/canny paths to lock morphology,
especially for monster and non-humanoid lanes.

Current Nymphs reality:

```text
Z-Image/Nunchaku txt2img works.
Z-Image Turbo LoRA loading works with normalized transformer-local LoRA keys.
Z-Image/Nunchaku controlnet_edit works in dev sanity tests after the Nunchaku
RoPE packing fix.
Sprite Generate + Process can use selected source images as ControlNet guides.
```

Do not call this full Sprite Foundry ControlNet parity yet. It is a working
guided generation path, not a completed morphology/depth/canny parity system.

Likely next backend work:

```text
generate source candidates
  -> guide directions with controlnet_edit
  -> compare consistency across all 8 directions
  -> derive depth with Depth Anything
  -> derive normals from depth
  -> decide whether additional canny/depth conditioning is needed
```

## Image Strip / Browser

Sprite's strip is now intentionally close to Nymphs Image:

- recent/date/folder views
- selected output object tracking
- visible-output selection helpers
- move selected to folder
- delete selected/folder
- manual folder picker
- select current/all/clear
- selected images feed `Generate + Process`

The intentionally missing Nymphs Image actions are only the Image-specific
"use selected as source/parts source" helpers. In Sprite, selection already
feeds `Generate + Process`, so do not add extra source buttons unless the user
asks for a clearer explicit action.

The Recent strip data source is now served by Sprite's own local UI server:

```text
GET  http://127.0.0.1:8098/api/outputs?limit=80
GET  http://127.0.0.1:8098/outputs/<source>/<relative-path>
POST http://127.0.0.1:8098/api/outputs/delete
POST http://127.0.0.1:8098/api/outputs/move
POST http://127.0.0.1:8098/api/outputs/folder/delete
```

Sources currently scanned:

```text
sprite:        $HOME/NymphsData/outputs/nymphs-sprite
zimage:        $HOME/NymphsData/outputs/zimage
zimage-legacy: $HOME/Z-Image/outputs
zimage-dev:    $HOME/NymphsModules/zimage/outputs
module:        <module-root>/outputs
```

Do not return to `file://` URLs or Manager `list_outputs` for the main UI
gallery. Keep copying Nymphs Image's output object shape and strip behavior.

## Validation Done This Session

Static checks passed:

```bash
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/nymph.json
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/_nymphs_sprite_common.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_list_zimage_outputs.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_open_ui.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_status.sh
python3 -m py_compile /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_ui_server.py
python3 -m py_compile /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.py
node inline-script parse check for ui/manager.html
```

Status check with source install root showed:

```text
downloaded_loras=mks0813_pixel_art,skyasl_pixel_artist,tarn59_pixel_art
selected_lora_candidate=mks0813_pixel_art
selected_lora_path=/home/nymph/LoRA/loras/mks0813_pixel_art/mks0813_pixel_art.safetensors
zimage_weight_profile_selected=int4_r32
zimage_weight_profile_ready=true
zimage_nunchaku_rank=32
zimage_nunchaku_precision=int4
```

Direct Nunchaku isolation showed:

```text
local r32 Nunchaku weight loads as rank 32
normalized mks LoRA applies successfully
unmatched_prefix_count=0
```

ControlNet/dev sanity:

```text
Nunchaku fork backup branch: backup/pre-zimage-controlnet
Nunchaku RoPE fix pushed: b092d6904f6ace0cc6fa65f3ac0beb1cf257ac40
Z-Image controlnet_edit smoke output succeeded in dev WSL.
Sprite Generate + Process with selected source image succeeded in dev WSL.
```

Sprite local UI server route checks:

```text
GET /health -> 200 JSON
GET /server_info -> 200 JSON
GET /nymph -> 200 HTML
GET /ui/nymphs_preview_forest.png -> 200 image/png
GET /api/outputs?limit=5 -> 200 JSON records
GET /outputs/<source>/<image>.png -> 200 image/png
POST /api/outputs/delete -> 200; removed image + metadata in temp root
POST /api/outputs/move -> 200; moved image + metadata in temp root
POST /api/outputs/folder/delete -> 200; removed temp managed folder
```

No Sprite UI server process was left running at the end of the route tests.

## Next Session Plan

1. Do not restart the architecture. The source-image step worked. Keep Sprite
   using shared Nymphs Image/Z-Image runtime and copy Nymphs Image behavior
   where practical instead of creating another backend.

2. Re-read this handoff and the module rules:

```text
/home/nymph/NymphsCore/docs/SUPERHIVE_RELEASE_CHECKLIST.md
/home/nymph/NymphsCore/docs/NYMPHS_MODULE_UI_STANDARD.md
/home/nymph/NymphsCore/docs/NYMPHS_MODULE_MAKING_GUIDE.md
```

3. Confirm the source repo is clean and raw manifest is public.

```bash
git -C /home/nymph/NymphsModules/nymphs-sprite status --short --branch
curl -L -s https://raw.githubusercontent.com/nymphnerds/nymphs-sprite/main/nymph.json | python3 -m json.tool
```

4. Test through Manager/module flow only.

- Install/update from Manager, not manual copy.
- Confirm installed Sprite version marker reports the pushed version.
- Open Sprite UI from Manager.
- Confirm no `Foundry Run` button in the left workflow.
- Confirm no visible `Foundry Status` action in the Manager action row.
- Confirm the Runtime controls show `Z-Image`, `Refresh`, and `Check` on the
  first row, with `Open Outputs` as its own full-width second row.
- Confirm the output strip `...` menu contains only Choose Folder, Move
  Selected, and Delete Folder.
- Confirm Recent thumbnails render actual images.
- Select output(s), then test Delete selected.
- Move selected output(s) to a folder.
- Delete that top-level managed folder.
- Generate Sources.
- Select a source image.
- Generate + Process for at least one direction.
- Then test all 8 directions.

5. If Manager testing passes, continue product cleanup.

- Rename the cryptic left-panel labels into clearer user steps.
- Consider moving dev-only Foundry entrypoints out of visible capabilities if
  Manager exposes capabilities directly elsewhere.
- Improve source-selection clarity: make it obvious selected strip images are
  guides for `Generate + Process`.
- Add output labels/filters that distinguish source images from processed
  sprite batches.

6. After Manager baseline is stable, choose the next feature:

```text
A. Full Foundry review/accept/reject/regenerate lifecycle
B. Depth/normal map production from accepted sprite sources
C. ControlNet consistency/morphology refinement across all 8 directions
D. Deterministic Foundry-style export pack once review/accept exists
```

Recommended next feature: make the current 8-direction ControlNet flow feel
usable and understandable before adding more Foundry lifecycle concepts.

## Test Commands

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

Sprite status from source checkout:

```bash
NYMPHS_SPRITE_INSTALL_ROOT=/home/nymph/NymphsModules/nymphs-sprite \
  /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_status.sh
```

Direct LoRA normalization smoke:

```bash
NYMPHS_SPRITE_INSTALL_ROOT=/home/nymph/NymphsModules/nymphs-sprite \
  /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_fetch_lora.sh \
  --candidate mks0813_pixel_art
```

Expected important lines:

```text
lora_candidate=mks0813_pixel_art
lora_path=/home/nymph/LoRA/loras/mks0813_pixel_art/mks0813_pixel_art.safetensors
lora_normalized=True
lora_ranks=32
```

## Rules To Preserve

- Source work happens in the dev/source checkout.
- Managed/test WSL is for end-user testing only.
- Do not manually sync files into the test WSL.
- Do not manually edit installed module files, markers, cached manifests, or
  runtime state.
- Module install/update scripts own installed `nymph.json` and
  `.nymph-module-version`.
- The marker is the installed-version source of truth.
- Publish module first, verify raw `nymph.json`, then update registry.
- Never advertise a version that is not pushed and raw-available.
- Keep fetched models out of git.
- Keep shared backend models in the shared Nymphs cache.
- Keep Sprite LoRAs in the shared LoRA library.
- Keep the original Foundry roster pure.
- Do not add ComfyUI or SDXL as dependencies.
- Do not claim ControlNet parity, mesh, GLB, or full Foundry export until each
  path is proven by an actual module test.
