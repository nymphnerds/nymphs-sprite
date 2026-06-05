# Nymphs Sprite Handoff

Last updated: 2026-06-05

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
nymphs-sprite 0.1.20
```

Current source tree has uncommitted changes. Do not update the registry until:

1. The source diff is reviewed.
2. The module repo is committed and pushed.
3. The raw GitHub `nymph.json` is verified.
4. Only then update the dev registry.

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

## Current Diff Summary

At this checkpoint, `nymphs-sprite` source has modified:

```text
CHANGELOG.md
README.md
docs/FOUNDRY_SOURCE_AUDIT_AND_TEST_FLOW.md
docs/SPRITE_HANDOFF.md
nymph.json
profiles/zimage_turbo_lora_candidates.json
scripts/_nymphs_sprite_common.sh
scripts/nymphs_sprite_delete_models.sh
scripts/nymphs_sprite_fetch_assets.sh
scripts/nymphs_sprite_fetch_lora.sh
scripts/nymphs_sprite_foundry_generate.sh
scripts/nymphs_sprite_generate_directions.py
scripts/nymphs_sprite_generate_directions.sh
scripts/nymphs_sprite_select_lora.sh
scripts/nymphs_sprite_status.sh
ui/manager.html
```

No untracked `__pycache__` artifacts were left after static checks.

High-level changes in that diff:

- Adds/normalizes three Z-Image Turbo pixel-art LoRAs.
- Moves Sprite LoRAs to the shared LoRA module layout.
- Stops using a private legacy Sprite LoRA subdirectory.
- Resolves stale selected-LoRA paths back to shared canonical paths.
- Makes Sprite status expose the selected Nymphs Image/Z-Image rank and
  precision.
- Makes Sprite UI/module generation call "load selected Z-Image model first"
  using the same pattern as Nymphs Image.
- Removes the fallback that silently avoided `mks0813_pixel_art`.
- Keeps ControlNet/Depth as staged assets only, not as a claimed working
  generation path.

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

Sprite now follows that pattern in both routes:

- direct browser/Z-Image route in `ui/manager.html`
- module bridge route in `scripts/nymphs_sprite_generate_directions.py`

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

During diagnosis, the dev installed Z-Image venv was inspected and briefly
repaired enough for direct tests. The durable fix should be through source and
module update, not manual venv edits.

Known source/runtime drift:

- `NymphsModules/zimage/model_manager.py` resolves the selected Nunchaku rank
  file to the exact local HF cache path before `from_pretrained`.
- `/home/nymph/Z-Image/model_manager.py` may be older and may still pass the
  repo/file string directly.

Next session should update installed Nymphs Image through the module update
flow before judging Sprite in managed/test runtime.

Also note:

- Local `/home/nymph/nunchaku` has newer Z-Image LoRA converter code.
- Building/reinstalling the Nunchaku fork from source is slow and was not
  completed in this session.
- Do not promise ControlNet or new Nunchaku fork behavior until it is built,
  installed through the proper script, and tested.

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
```

Implemented pieces:

- Nymphs Image-style Manager visual language.
- Original Foundry roster preset dropdown.
- Three shared LoRA choices.
- Fast source generation path through Z-Image `/generate`.
- Model-load-first behavior copied from Nymphs Image.
- Module-action fallback for bridge cases.
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
/home/nymph/NymphsModules/sprite-foundry/bakeoff/<run_id>
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
- Foundry run browser/status board in Sprite UI

Missing backend parity:

- Real Z-Image ControlNet/morphology conditioning is not proven.
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
Z-Image ControlNet assets can be fetched.
No working Z-Image ControlNet pipeline path has been proven in the current
Nymphs Image runtime.
```

Do not promise ControlNet parity until a real Nymphs Image backend path works.

Likely short-term fallback:

```text
generate albedo/source first
  -> derive depth with Depth Anything
  -> derive normals from depth
  -> use post-process / Qwen-edit-style refinement where useful
  -> revisit ControlNet when Nunchaku or diffusers exposes a usable Z-Image path
```

## Image Strip / Browser

Nymphs Image has a stronger strip browser than Sprite:

- recent/date/folder views
- selected output object tracking
- visible-output selection helpers
- move selected to folder
- delete selected/folder
- refresh output gallery
- use selected as source

Sprite currently has a simpler strip:

- recent output load via module `list_outputs`
- manual folder picker
- select current/all/clear
- selected images feed `Generate + Process`

Do not port the full Nymphs Image strip browser in the current cleanup unless
explicitly requested. The user likes it, but we paused this to keep the current
fix scoped. Future polish should copy the tested Nymphs Image pattern rather
than inventing a new browser.

## Validation Done This Session

Static checks passed:

```bash
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/nymph.json
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/profiles/zimage_turbo_lora_candidates.json
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_fetch_lora.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_status.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_foundry_generate.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_fetch_assets.sh
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_select_lora.sh
python3 -m py_compile /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.py
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

No Z-Image/API server process was left running at the end of the session.

## Next Session Plan

1. Re-read this handoff and the module rules:

```text
/home/nymph/NymphsCore/docs/SUPERHIVE_RELEASE_CHECKLIST.md
/home/nymph/NymphsCore/docs/NYMPHS_MODULE_UI_STANDARD.md
/home/nymph/NymphsCore/docs/NYMPHS_MODULE_MAKING_GUIDE.md
```

2. Review the source diff.

```bash
git -C /home/nymph/NymphsModules/nymphs-sprite status --short --branch
git -C /home/nymph/NymphsModules/nymphs-sprite diff --stat
git -C /home/nymph/NymphsModules/nymphs-sprite diff -- scripts/nymphs_sprite_fetch_lora.sh ui/manager.html scripts/nymphs_sprite_generate_directions.py scripts/nymphs_sprite_status.sh
```

3. Confirm Z-Image source/runtime alignment.

- Check whether installed `/home/nymph/Z-Image` is behind `NymphsModules/zimage`.
- If behind, update it through module update flow.
- Do not manually patch installed runtime files.
- Confirm `model_manager.py` uses exact local HF cache path resolution for
  Nunchaku rank weights.

4. Run static checks again.

```bash
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/nymph.json
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/profiles/foundry_character_presets.json
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/profiles/zimage_turbo_lora_candidates.json
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/*.sh
python3 -m py_compile /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.py
```

5. Test through Manager/module flow only.

- Install/update from module manager.
- Run `Model Fetch -> Complete Sprite Stack`.
- Confirm all three LoRAs appear in dropdown.
- Confirm selected LoRA is `mks0813_pixel_art`.
- Confirm selected path is in `$HOME/LoRA/loras/mks0813_pixel_art/`.
- Confirm Z-Image selected model loads before generation.
- Generate one enabled preset, preferably `Goblin Scout`.
- Try one backup LoRA if mks output is stylistically poor, but do not remove mks.

6. If generation works, commit and push `nymphs-sprite`.

- Verify raw `nymph.json` at GitHub.
- Only then update dev registry.
- Do not touch public/production registry.

7. After the working baseline is pushed, choose the next feature:

```text
A. Full Foundry review/accept/reject/regenerate lifecycle
B. Nymphs Image strip browser/picker port
C. ControlNet/Nunchaku backend research spike
D. Depth/normal map production from accepted sprite sources
```

Recommended next feature: A, then B. ControlNet should remain research until a
working backend path is proven.

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
