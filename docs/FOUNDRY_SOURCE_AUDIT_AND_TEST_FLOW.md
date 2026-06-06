# Foundry Source Audit And Test Flow

Last updated: 2026-06-06

## Scope

This note compares three code lines:

- Original upstream Sprite Foundry: `mcp-tool-shop-org/sprite-foundry`, local `upstream/main` at `0a05af9`.
- Nymphs Foundry fork: `nymphnerds/sprite-foundry`, local `main` at `fb43975`.
- Nymphs Sprite module: `nymphnerds/nymphs-sprite`, local source prepared as
  `0.1.20`.

The goal is to make `nymphs-sprite` feel as close as possible to the original Foundry flow, including Foundry character presets, while using Nymphs-owned generation backends.

## Original Foundry Flow

Upstream Sprite Foundry is a full local production pipeline, not just an image generator:

```text
Subject Sheet
  -> ComfyUI Generation (SDXL + LoRA + ControlNet)
  -> Mechanical Gates
  -> Raw/Pixel Review
  -> Normal + Depth Map Generation
  -> Godot Finish Lab
  -> Deterministic Export
```

Core contracts:

- 8 directions: `front`, `front_left`, `left`, `back_left`, `back`, `back_right`, `right`, `front_right`.
- SQLite registry for subjects, runs, attempts, artifacts, reviews, gate results, and lineage.
- Mechanical gates check count, dimensions, transparency, and artifact validity.
- Human review is explicit: `review-show`, `review-accept`, `review-reject`, `regen`.
- Production closeout is explicit: `produce`, `finish-board`, `export`.
- Export contract is deterministic: `albedo/`, `normal/`, `depth/`, `preview/`, `manifest.json`, checksums, provenance.
- Public roster target is 92 production packs across 12 lanes.

The original backend dependency is ComfyUI. Non-humanoid and monster-lane work uses body-class ControlNet depth references to lock silhouette and morphology.

## Nymphs Foundry Fork

The fork is the closest code path to the desired final behavior. It keeps the Foundry lifecycle and swaps only the generation backend.

Added or changed relative to upstream:

- `pipeline/nymphscore_client.py`: small HTTP client for Nymphs Image.
- `pipeline/foundry_gen_nymphscore.py`: Z-Image generation runner that writes raw/pixel artifacts and registers them in Foundry.
- `foundry/cli.py`: adds `generate-nymphscore`.
- `pipeline/foundry_maps.py`: follows the run `sprite_target` instead of hard-coding `48`.
- `verify.sh`: updated and passes locally.

The main generation command is:

```bash
cd /home/nymph/NymphsModules/sprite-foundry
python3 -m foundry.cli generate-nymphscore \
  --config pipeline/chars/goblin_scout.json \
  --nymphscore-url http://127.0.0.1:8090 \
  --sprite-size 96 \
  --width 1024 \
  --height 1024 \
  --steps 9
```

That command:

- Calls Nymphs Image `POST /generate`.
- Uses `Tongyi-MAI/Z-Image-Turbo`.
- Supports LoRA path, trigger, scale, Nunchaku rank, Nunchaku precision, size, seed, and palette controls.
- Writes `bakeoff/{run_id}` raw images, pixel sprites, contact sheets, `recipe.json`, and `manifest.json`.
- Registers the run and each attempt in the Foundry DB.
- Runs `foundry check` unless `--no-check` is passed.
- Leaves the user at `foundry review-show {run_id}`.

Local verification passed:

```text
OK: foundry module imports
OK: 8 directions, 13 states, schema v2
OK: CLI parser builds
Packs checked: 44
OK: roster_index.json - 92 packs
All checks passed.
```

## Nymphs Sprite Current State

`nymphs-sprite` is currently a Manager-hosted module UI and sprite batch processor. It is not yet a Manager wrapper around the full Foundry lifecycle.

What exists now:

- Installed module path: `/home/nymph/Nymphs-Sprite`.
- Installed/runtime version may lag source until the module commit is pushed,
  raw `nymph.json` is verified, and the dev registry is updated.
- Custom Manager UI: `ui/manager.html`.
- Module actions for status, asset fetch, LoRA selection, source generation, post-processing, output browsing, and logs.
- Z-Image source generation through direct `POST /generate`, with a Manager-action fallback.
- Foundry-style post-process:
  - copy raw source image
  - remove green-screen/background
  - crop/pad foreground to square
  - nearest-neighbor resize to `sprite_size`
  - write transparent albedo
  - write previews/contact sheets
  - run basic source and mechanical checks
- Batch manifest: `sprite_batch.json` with schema `nymphs-sprite.batch.v1`.
- Foundry presets now imported into:
  - `profiles/foundry_character_presets.json` with the original 92-pack roster
    only; 51 entries currently have matching generation prompt configs in the
    local fork
  - `profiles/foundry_export_roster.json` with the same 92-pack roster target

What is missing for close Foundry parity:

- No Foundry SQLite registry in the module flow.
- No `subject-add`, `register-run`, or `register-attempt` bridge from module batches into Foundry.
- No raw/pixel accept/reject states.
- No `regen` loop.
- No current `produce` path for normal/depth maps. Continue without this for
  now; do not create `normal/` or `depth/` folders in active Sprite output.
- No Godot finish-lab bridge.
- No deterministic Foundry export command from the module UI.
- No body-class morphology/control path yet through Z-Image ControlNet Union.
- No Manager actions for Foundry status, review, accept, reject, produce, or export.

## Current Failure Diagnosis

The current failure mode has three separate layers:

1. Source/available/installed drift.
   - Local source can be ahead of the Manager-visible remote version until the
     module commit is pushed and the registry points to the verified raw
     manifest.
   - Installed runtime state can therefore show old fetch dropdowns and old
     selected paths even when source has moved on.

2. Legacy LoRA path drift.
   - Older versions selected files under
     `$HOME/LoRA/loras/nymphs-sprite/<repo-slug>/...`.
   - The forward contract is the LoRA module layout:
     `$HOME/LoRA/loras/<lora-id>/<lora-id>.safetensors`.
   - `0.1.20` resolves stale selected candidates back to the shared library
     before both fast source generation and Foundry bridge generation.

3. Z-Image/Nunchaku LoRA key format.
   - Public Z-Image LoRAs use inconsistent key roots:
     `base_model.model.`, `diffusion_model.`, adapter-name `.default` segments,
     or already-local transformer keys.
   - Nunchaku's Z-Image mapper expects transformer-local keys such as
     `layers.0.attention.to_q.lora_A.weight`.
   - `0.1.20` normalizes fetched starter LoRAs into the shared LoRA-library
     runtime copy and records source/rank metadata next to the file.

The module should not treat these as one generic generation failure. Status and
logs should make it clear whether the blocker is version drift, asset
readiness, selected path drift, Z-Image model load, or backend LoRA application.

## Recommendation

Treat `sprite-foundry` as the canonical lifecycle engine and `nymphs-sprite` as the Manager workbench.

The next architecture step should be to add Foundry bridge actions to `nymphs-sprite` instead of reimplementing Foundry review/export in JavaScript:

```text
Nymphs Sprite UI
  -> Foundry bridge action
  -> python3 -m foundry.cli generate-nymphscore
  -> Foundry DB + bakeoff artifacts
  -> module UI displays review boards and run status
  -> Foundry accept/reject/produce/export actions
```

Suggested new module actions:

- `foundry_status`: call `python3 -m foundry.cli status`.
- `foundry_generate`: call `python3 -m foundry.cli generate-nymphscore`.
- `foundry_review_show`: call `python3 -m foundry.cli review-show <run_id>`.
- `foundry_accept`: call `python3 -m foundry.cli review-accept <attempt_id>`.
- `foundry_reject`: call `python3 -m foundry.cli review-reject <attempt_id> --code <code>`.
- `foundry_produce`: call `python3 -m foundry.cli produce <run_id>`.
- `foundry_export`: call `python3 -m foundry.cli export <run_id> --overwrite`.

Keep backend adapters inside Foundry pipeline scripts where possible. The module UI should select presets, LoRAs, sizes, and review decisions; Foundry should own lifecycle, registry, gates, provenance, and exports.

Current decision for Nymphs Sprite: do not reintroduce ComfyUI to get
normal/depth maps. The active module workflow stops at generated sources,
cleaned transparent albedo sprites, contact/inspection previews, and
`sprite_batch.json`. Future map work can investigate local Nymphs-owned nodes:

```text
accepted/processed sprite
  -> local Depth Anything
  -> local normal-from-depth or standalone normal estimator
  -> optional maps bundle
```

Until that exists and is tested, normal/depth are future-plan items only.

## Test Flow

### 0. Static Source Checks

Run these after any source edit:

```bash
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/nymph.json
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/profiles/foundry_character_presets.json
python3 -m json.tool /home/nymph/NymphsModules/nymphs-sprite/profiles/foundry_export_roster.json
bash -n /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.sh
python3 -m py_compile /home/nymph/NymphsModules/nymphs-sprite/scripts/nymphs_sprite_generate_directions.py
bash /home/nymph/NymphsModules/sprite-foundry/verify.sh
```

Expected:

- JSON parses.
- Shell and Python syntax pass.
- Foundry verify reports all checks passed and roster index is 92 packs.

### 1. Module Install And Readiness

```bash
bash /home/nymph/NymphsModules/nymphs-sprite/scripts/install_nymphs_sprite.sh
bash /home/nymph/Nymphs-Sprite/scripts/nymphs_sprite_status.sh
```

Expected before asset fetch:

```text
installed=true
runtime_present=true
state=model_download_needed
weight_profile_ready=false
```

Expected after model fetch:

```text
models_ready=true
assets_ready=true
downloaded_loras=...
weight_profile_ready=true
```

### 2. Model Fetch

In Manager, use `Model Fetch -> Complete Sprite Stack`.

CLI equivalent:

```bash
bash /home/nymph/Nymphs-Sprite/scripts/nymphs_sprite_fetch_assets.sh --asset complete_sprite_stack
bash /home/nymph/Nymphs-Sprite/scripts/nymphs_sprite_status.sh
```

Expected:

- At least one Z-Image Turbo pixel-art LoRA exists under `/home/nymph/LoRA/loras/<lora-id>/<lora-id>.safetensors`.
- `lora_choices` is not `none`.
- `selected_lora_candidate` is usable.

### 3. Start Nymphs Image / Z-Image

Start Z-Image from Manager with `Open Z-Image` or module action `start_zimage`, then verify:

```bash
curl -s http://127.0.0.1:8090/server_info
curl -s http://127.0.0.1:8090/api/loras
```

Expected:

- `server_info` returns JSON.
- `/api/loras` returns the selected sprite LoRA or another usable LoRA path.

### 4. Nymphs Sprite Source Smoke Test

Use the Manager UI:

1. Choose the `goblin_scout` Foundry preset.
2. Select the downloaded pixel-art LoRA.
3. Check only `front`.
4. Click `Generate Sources`.

Expected:

- One Z-Image source image appears in the stage/strip.
- No `Connection timed out` or `no LoRA path` error appears.
- The image uses a bright green or easily removable background.

Then click `Generate + Process`.

Expected:

- A batch appears under `/home/nymph/NymphsData/outputs/nymphs-sprite/goblin_scout/`.
- `sprite_batch.json` exists.
- `preview/contact_sheet.png` exists.
- `albedo/01_front.png` exists, is transparent, and is `sprite_size` square.

### 5. Nymphs Sprite Full Direction Test

Repeat the UI test with all 8 directions checked.

Expected:

- 8 generated source images.
- 8 processed albedo sprites.
- `sprite_batch.json` records `processed_count=8`.
- Mechanical pass count is visible in the manifest.

### 6. Foundry Fork Canonical Test

Run the lifecycle path directly against the Foundry fork:

```bash
cd /home/nymph/NymphsModules/sprite-foundry
python3 -m foundry.cli init
python3 -m foundry.cli generate-nymphscore \
  --config pipeline/chars/goblin_scout.json \
  --nymphscore-url http://127.0.0.1:8090 \
  --sprite-size 96 \
  --width 1024 \
  --height 1024 \
  --steps 9
```

Expected:

- `bakeoff/{run_id}` is created.
- Raw and pixel contact sheets are created.
- Foundry registers the run and attempts.
- `foundry check` runs.
- The command prints `Next: foundry review-show {run_id}`.

Then:

```bash
python3 -m foundry.cli review-show <run_id>
```

Expected:

- Review queue shows generated/check-passed attempts for visual decision.

### 7. Future Review, Produce, Export Test

After visual review, accept one complete 8-direction run:

```bash
python3 -m foundry.cli batch-accept <run_id>
python3 -m foundry.cli produce <run_id>
python3 -m foundry.cli finish-board <run_id>
python3 -m foundry.cli batch-accept <run_id>
python3 -m foundry.cli export <run_id> --overwrite
```

Expected for the future Foundry bridge, not the current Sprite UI:

- If map production is enabled, it must use local non-ComfyUI module code.
- Until that exists, no `normal/` or `depth/` folders should be emitted by the
  active Sprite workflow.
- Export work should write only proven assets and should not advertise map
  layers that were not generated.

## Definition Of Done For Foundry Parity

`nymphs-sprite` is Foundry-parity enough when a user can do this from Manager:

```text
select Foundry preset
  -> select Z-Image LoRA/backend
  -> generate 8 sources
  -> inspect raw/pixel contact sheets
  -> accept/reject/regen attempts
  -> optionally produce maps only after local non-ComfyUI map nodes exist
  -> finish review board
  -> export deterministic Foundry pack
```

And the filesystem/registry results match the original Foundry contract:

- Foundry DB has subjects, runs, attempts, artifacts, reviews, and gates.
- `bakeoff/{run_id}` contains raw, pixel, recipe, manifest, and review sheets.
- Current Sprite exports/batches contain generated sources, cleaned albedo
  sprites, previews, and manifest/provenance only.
- Future full Foundry export can add `normal` and `depth` only after local
  non-ComfyUI map derivation is implemented and tested.
- Sprite size is recorded and honored; it is not silently forced to 48.
