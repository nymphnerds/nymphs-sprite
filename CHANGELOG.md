# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.2.8] - 2026-06-09

### Changed

- Rebased the stale `nymphs-sprite` module on the evolved Sprite Foundry module.
- Renamed the user-facing module identity to **Nymphs Sprite** while keeping the
  repository as `nymphnerds/nymphs-sprite`.
- Updated module install/runtime/data defaults to use `$HOME/Nymphs-Sprite`,
  port `8098`, and `$HOME/NymphsData/*/nymphs-sprite`.
- Began the distilled workflow UI: Character, Guide, Style, Generate, Review,
  with inherited Foundry lifecycle controls moved into Advanced.

## [1.2.7] - 2026-06-07

### Fixed

- NymphsCore/Z-Image generation now writes final Sprite Foundry images directly
  to `$HOME/NymphsData/outputs/sprite-foundry/<subject_id>/` with simple names
  such as `front.png`, `front_raw.png`, and `contact_sheet.png`.
- `Open Outputs` now opens `$HOME/NymphsData/outputs/sprite-foundry`.
- The UI now updates progress direction by direction during generation.
- Generation now fails fast with a clear message when the selected LoRA cannot
  attach to the current Z-Image/Nunchaku transformer.

## [1.2.6] - 2026-06-06

### Fixed

- Sprite Foundry generation now starts the selected Nymphs Image / Z-Image
  backend automatically before running the Foundry `generate-nymphscore` path.
- The workbench no longer blocks Generate merely because the backend is stopped
  when required weights and LoRAs are present.
- Replaced the dead Runtime `Foundry` button with an explicit `Start Backend`
  action and made `Check` show its status output instead of silently swallowing
  it.
- Status/details wording now says Generate will start the backend automatically.

## [1.2.5] - 2026-06-06

### Fixed

- Sprite Foundry LoRA fetch now preserves Hugging Face repo/file identity in
  the shared LoRA folder instead of renaming downloaded LoRAs. The three bundled
  pixel-art LoRAs are written as:
  - `$HOME/LoRA/loras/mks0813--z-image-turbo-pixel-art-lora/z-image-turbo-pixel-art-lora.safetensors`
  - `$HOME/LoRA/loras/SkyAsl--Pixel-artist-Z/adapter_model.safetensors`
  - `$HOME/LoRA/loras/tarn59--pixel_art_style_lora_z_image_turbo/pixel_art_style_z_image_turbo.safetensors`
- Sprite Foundry status and UI LoRA choices now show those actual downloaded
  LoRA names rather than friendly replacement labels. Custom user LoRAs in
  `$HOME/LoRA/loras` are also shown by their real folder/file name.
- Sprite Foundry LoRA downloads now emit the standard compact NymphsCore
  `MODEL FETCH STARTED/STATUS/COMPLETE` progress lines instead of raw path-only
  output.
- `delete_models` now deletes the corrected HF-shaped LoRA files and also
  cleans up the exact old renamed Sprite Foundry LoRA paths if present.

## [1.2.4] - 2026-06-06

### Changed

- Expanded Sprite Foundry's own Details page `Model Fetch` dropdown so users
  can fetch the full starter stack, ControlNet, all bundled pixel-art LoRAs, or
  individual Sprite Foundry LoRAs from Sprite Foundry itself.
- Sprite Foundry LoRA fetch now writes to the shared LoRA module folder:
  `$HOME/LoRA/loras`.
- The starter stack fetch delegates the shared Z-Image INT4 r32/backend weight
  fetch to Nymphs Image, fetches ControlNet 2.1, and installs the recommended
  Z-Image Turbo Pixel LoRA into the shared LoRA folder.
- Details-page cache reporting now includes the Sprite Foundry LoRA profiles as
  downloaded when their shared LoRA files are present.
- `delete_models` can now delete the known Sprite Foundry LoRA profiles from
  the shared LoRA folder without touching datasets, jobs, outputs, logs, or
  unrelated trained LoRAs.

## [1.2.3] - 2026-06-06

### Fixed

- Fixed `foundry_generate` rejecting UI-encoded `--lora-trigger-b64-*`
  arguments before generation could reach Z-Image/Nunchaku.
- Fixed the Foundry CLI bridge for direction review actions. The UI can still
  work by run ID and direction, but the wrapper now resolves that selection to
  the real attempt ID expected by `foundry review-accept` and
  `foundry review-reject`.
- Fixed the `subject-add` bridge command to match the real Foundry CLI
  signature.
- Added Sprite Foundry status reporting for Z-Image install/running/model state
  and available Z-Image pixel-art LoRAs, so the workbench no longer guesses
  backend readiness.
- Disabled generation until ControlNet, Z-Image models, Z-Image backend, and a
  selectable LoRA are ready.
- Disabled run-scoped Foundry lifecycle buttons until a run ID exists, replacing
  the previous `--run-id is required` trap.
- Expanded run ID parsing to understand both `Run:` and `run_id:` output.

## [1.2.2] - 2026-06-06

### Changed

- Removed the generic Manager details-page generation form. Generation method
  selection belongs inside the module-owned Sprite Foundry UI.
- Removed raw `Foundry Status` and `Foundry Command` buttons from the normal
  Manager details page. Those are internal workflow tools, not standard module
  detail actions.
- Added an explicit `Open UI` installed action so the Manager details page opens
  the real Nymphs-style Sprite Foundry workbench.
- Added a Sprite Foundry-owned details-page `Model Fetch` action for
  `Fetch ControlNet`. It delegates to Nymphs Image for the shared Z-Image
  ControlNet 2.1 weight, but the user workflow starts from Sprite Foundry.
- Added the standard optional Hugging Face token field to Sprite Foundry's
  details-page `Model Fetch` group.
- Changed details-page `Open Outputs` and `Logs` actions to the same result
  modes used by other Nymphs modules.
- Added Sprite Foundry status cache reporting so the details page shows
  `sprite_foundry_controlnet_2_1` as downloaded after the shared ControlNet
  weight is fetched.
- Added a scoped `delete_models` action for the same profile so the details-page
  cache chip can delete only that ControlNet weight.
- Updated the local URL launch output to include `module_ui_url=...` per the
  Nymphs module guide.

## [1.2.0] - 2026-06-06

### Added

- **NymphsCore module identity** — added `nymph.json` with `id: sprite-foundry`,
  user-facing name `Sprite Foundry`, repo `nymphnerds/sprite-foundry`, install
  root `$HOME/Sprite-Foundry`, and module-owned Manager actions.
- **Lifecycle scripts** — added install, update, status, logs, outputs, Foundry
  status, and Foundry generation entrypoints under `scripts/`.
- **First-class Foundry generation commands** — exposed the existing generation
  paths through `foundry.cli`:
  - `generate-nymphscore`
  - `generate-stack-a-v2`
  - `generate-morph`
  - `generate-turnaround`
- **Explicit Manager generation control** — added a module action group that
  chooses one Foundry generation method inside the Sprite Foundry lifecycle
  instead of the previous confusing source/process split from the abandoned
  `nymphs-sprite` module.
- **Nymphs workbench UI** — added a local-url Nymphs UI with generation-method
  selection, Foundry lifecycle controls, and a full output strip for Foundry
  artifacts.
- **Foundry CLI bridge** — added a constrained module action for real Foundry
  lifecycle commands such as check, review, accept/reject, produce, export,
  lineage, drift, and metrics.
- **Standard Manager UI contract** — the module manifest now declares the
  `local_url` title, start action, and stop action used by the NymphsCore
  lifecycle rail.
- **Standard outputs action** — `open_outputs` now returns `directory=...` like
  the other Nymphs modules.

### Changed

- Reframed the NymphsCore module as **Sprite Foundry**, not Nymphs Sprite.
- Treats Z-Image/Nunchaku as the NymphsCore backend path for Foundry generation,
  not as the user-facing workflow.
- The NymphsCore generation path now directs Z-Image backend output into a
  Sprite-Foundry-owned run folder and moves it into `bakeoff/<run_id>/`, avoiding
  duplicate visible Z-Image batches.

## [1.1.0] - 2026-03-27

### Added

- **Monster Lane** — pipeline extension for non-humanoid sprites with 3 new body classes (amorphous, wide/squat, tall/thin)
- **Body Class Presets** — `body_class` field in character configs auto-selects depth refs, ControlNet strength, and timing
- **3 New Depth Ref Generators** — `gen_amorphous_depth.py`, `gen_wide_squat_depth.py`, `gen_tall_thin_depth.py`
- **Body-Class-Aware Gates** — `single_subject` gate uses relaxed thresholds for wide body classes
- **6 Beast Export Packs** — Rat King, Lantern Angler, Grinning Idol, Spore Mother, Root Puppet, Mud Revenant
- **`--body-class` CLI Flag** — override body class from command line for `foundry_gen_morph`

### Changed

- Roster expanded to 82 production packs (added townsfolk, goblin, hero, pirate, villain, zombie, and beast lanes)
- Background removal uses dual-corner sampling to handle ground planes
- Scene setting stripped from beast prompts for clean bg removal
- `run_all_gates` and `gate_single_subject` accept optional `body_class` parameter
- `cmd_check` auto-resolves body class from character config JSON

## [1.0.0] - 2026-03-26

### Added

- **Foundry CLI** — 20 commands for subject registration, run tracking, review workflow, export, and analytics
- **SQLite Registry** — append-only lifecycle tracking with 13 states, reject codes, regen lineage, schema v2
- **ComfyUI Generation Pipeline** — SDXL + pixel-art-xl LoRA + ControlNet (Depth + Canny), 8-direction 48px sprites
- **Morphology System** — arthropod, quadruped, and winged body families via depth/edge reference images
- **Mechanical Gates** — automated validation (transparency, direction count, dimension checks)
- **Normal + Depth Map Generation** — ComfyUI-derived maps for each accepted direction
- **Godot Finish Lab** — 4 lighting states × 8 directions = 32 captures per subject
- **Deterministic Export** — `foundry export <run_id>` emits packs with SHA-256 checksums and manifest.json
- **Export Contract v1.0.0** — frozen: 8 dirs, 48×48 transparent PNG, albedo/normal/depth layers, center_bottom pivot
- **Roster Index** — `exports/roster_index.json` with lane breakdown and file counts
- **20 Production Export Packs** — 7 crew, 6 creature, 3 hostile, 2 authority, 2 civilian
- **Bakeoff System** — comparative evaluation of generation stacks (A/B/C)
- **Batch Review** — `batch-accept` and `batch-reject` for high-throughput review
- **Drift Analysis** — failure pattern detection and pass rates across runs
- **Story + Lineage** — full provenance trail from subject registration through export
- **Subject Sheets** — per-character design specs with pose, palette, and morphology notes
