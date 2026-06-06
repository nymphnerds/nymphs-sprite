# Changelog

## 0.1.39 - 2026-06-06

- Clarify the active Sprite workflow: current batches produce source/raw,
  cleaned albedo sprites, preview/contact sheets, and manifests only.
- Mark depth/normal map production as future non-ComfyUI module work, not part
  of the current output contract.
- Document that Sprite should not create `normal/` or `depth/` folders until a
  local Nymphs-owned map derivation stage exists.

## 0.1.38 - 2026-06-06

- Move Open Outputs onto its own full-width Runtime row so the Z-Image,
  Refresh, and Check buttons no longer crowd the sidebar.

## 0.1.37 - 2026-06-06

- Move Open Outputs back to a first-class visible Runtime control and rename
  the Z-Image launcher so the two actions are not confused.
- Keep the output strip folder menu aligned with Nymphs Image: Choose Folder,
  Move Selected, and Delete Folder only. Select, Select All, Clear, and Delete
  remain visible strip actions.
- Document the current Sprite batch folder layout against original Sprite
  Foundry's bakeoff/export output shapes.

## 0.1.36 - 2026-06-06

- Refresh the Sprite handoff to match the pushed `0.1.35` UI/output-strip
  baseline, current Nunchaku/Z-Image ControlNet state, and next Manager test
  path.
- Clarify that Foundry-facing scripts are developer/audit tools and are not
  part of the normal user workflow.

## 0.1.35 - 2026-06-06

- Remove the legacy Foundry Run button, dead Foundry UI path, and visible
  Foundry Status Manager action from the main Sprite workflow.
- Add Nymphs Image-style output strip management: Move Selected, Delete Folder,
  and Delete selected images.
- Add Sprite local UI POST endpoints for `/api/outputs/delete`,
  `/api/outputs/move`, and `/api/outputs/folder/delete`, constrained to the
  managed output roots served by the Sprite UI.

## 0.1.34 - 2026-06-06

- Mirror the Nymphs Image output-browser contract in Sprite's `local_url` UI:
  the browser now refreshes Recent with same-origin `/api/outputs?limit=80`.
- Serve browsed Sprite and Z-Image files as same-origin `/outputs/<source>/...`
  URLs so thumbnails and the main preview render inside WebView2.
- Keep the legacy Manager `list_outputs` helper on the same `/outputs/...` URL
  scheme if it is called outside the UI.

## 0.1.33 - 2026-06-06

- Switch the Sprite Manager UI from `local_html` to the standard Nymphs
  `local_url` `/nymph` contract used by generation modules.
- Add the module UI runtime routes at `http://127.0.0.1:8098/nymph`,
  `/health`, and `/server_info`, with `open_nymph_ui` as the Manager start
  action.
- Serve `ui/nymphs_preview_forest.png` as a normal `/ui` asset instead of
  embedding it into the HTML, avoiding WebView2 local HTML size failures.
- Remove the duplicate in-page `Nymphs Sprite` title and keep the Manager
  shell header as the module title.

## 0.1.32 - 2026-06-06

- Wire selected/generated source images into Z-Image Nunchaku
  `controlnet_edit` for guided direction generation.
- Preserve the old selected-image post-processing behavior behind the
  `--source-mode process` CLI path while the Manager Generate + Process flow
  now uses `--source-mode controlnet`.
- Record `generation_mode`, `control_source_path`, and
  `controlnet_conditioning_scale` in `sprite_batch.json`.

## 0.1.31 - 2026-06-05

- Embed the forest PNG as a data URI during install/update so Sprite's
  `local_html` stage does not depend on Manager resolving relative file assets.
- Make the Recent strip use the same Nymphs Image output source by proxying
  `/api/outputs?limit=80`, with a filesystem fallback over:
  `$HOME/NymphsData/outputs/zimage`, `$HOME/Z-Image/outputs`, and
  `$HOME/NymphsModules/zimage/outputs`.

## 0.1.30 - 2026-06-05

- Restored the Nymphs Image forest stage look in Sprite by simplifying the
  viewer background to use the installed `ui/nymphs_preview_forest.png`
  directly.
- Removed the darker inherited overlay/fallback stack that made the stage read
  as a plain black panel in Manager.

## 0.1.29 - 2026-06-05

- Flush source-generation progress lines immediately from the Sprite bridge so
  Manager can show `batch_id`, `zimage_model_loaded`, and `generate=<direction>`
  while Z-Image/Nunchaku is working.
- Merge final Z-Image JSON preview URLs onto the existing local output path
  entries instead of adding a second duplicate strip tile.
- Keep the architecture unchanged: shared Nymphs Image/Z-Image runtime, shared
  venv/cache/LoRA library, no vendored backend.

## 0.1.28 - 2026-06-05

- Restored `generate_sources` as the Manager action transport for Sprite's
  `local_html` UI.
- Removed browser-side source-generation `fetch()` calls to the Z-Image API
  from the active path, avoiding WebView cross-origin `Failed to fetch`.
- Kept the backend shared with Nymphs Image/Z-Image: same installed runtime,
  same venv, same `$HOME/NymphsData/cache/huggingface` model cache, and same
  `$HOME/LoRA/loras` LoRA library.

## 0.1.27 - 2026-06-05

- Removed the Sprite `generate_sources` module action from the advertised
  manifest surface so Manager cannot route source image generation through the
  old script bridge.
- Kept the UI `Generate Sources` button, but it now only uses the direct
  Nymphs Image-style Z-Image `/generate` call.
- Matched the working Nymphs Image fast smoke-test defaults: `auto_r32`,
  512x512, 8 steps, seed 0, LoRA strength 1, and one `front` source selected
  by default.

## 0.1.20 - 2026-06-05

- Normalize fetched Z-Image LoRA keys into the runtime copy stored under the
  shared `$HOME/LoRA/loras/<id>/<id>.safetensors` library. This strips common
  PEFT/AI Toolkit prefixes such as `base_model.model.` and `diffusion_model.`
  so Nymphs Image's Z-Image/Nunchaku adapter mapper can consume the files.
- Preserve LoRA metadata with `normalized_for=zimage_nunchaku` and raw rank
  hints in `nymphs_lora.json`.
- Resolve stale legacy selected-LoRA paths to the current shared-library path
  before both fast source generation and the Foundry bridge run.
- Make status report the resolved selected LoRA path, so the Manager UI no
  longer shows old Sprite-private paths after updating.

## 0.1.19 - 2026-06-05

- Switched Sprite LoRA fetches to the LoRA module's shared
  `$HOME/LoRA/loras/<id>/<id>.safetensors` layout and writes
  `nymphs_lora.json` metadata next to each fetched LoRA.
- Updated the mks0813 candidate to the corrected
  `mks0813/z-image-turbo-pixel-lora` repository and keeps it selected after
  complete fetches.
- Added `SkyAsl/Pixel-artist-Z` as a character-focused backup LoRA while
  keeping `tarn59/pixel_art_style_lora_z_image_turbo` as the style fallback.
- Removes the old Sprite-private LoRA layout from the normal path; the shared
  LoRA module layout is now the forward-only storage contract.

## 0.1.18 - 2026-06-05

- Load the selected Z-Image Turbo INT4 r32 model through `/api/model/load`
  before calling `/generate`, fixing first-run failures where the server was
  online but no model was loaded.
- Fall back from stale `mks0813_pixel_art` LoRA selection to the downloaded
  runtime-compatible `tarn59_pixel_art` LoRA when present.
- Updated direct UI generation to use INT4 r32 and perform the same model-load
  preflight before generation.

## 0.1.17 - 2026-06-05

- Rebuilt `foundry_character_presets.json` from the original 92-entry Sprite
  Foundry export roster only, removing non-roster local character configs from
  the Manager dropdown.
- Kept original roster labels in the UI and disabled roster entries whose local
  Foundry prompt/source config is not available yet.
- Moved staged ControlNet and Depth Anything downloads onto the same shared
  Hugging Face cache convention used by Nymphs Image, TRELLIS, and Pixal3D.
- Made the module generation bridge auto-start Nymphs Image/Z-Image when the
  `/server_info` probe is offline, and made the UI fail over quickly instead
  of waiting on a dead `/generate` request.
- Updated manifest/docs to report shared model cache roots and the exact roster
  contract.

## 0.1.16 - 2026-06-05

- Added a Sprite-facing fetch bridge to the shared Nymphs Image / Z-Image model
  fetcher and Hugging Face cache.
- Collapsed Manager fetch UI to one compact `Model Fetch` dropdown, matching
  the other modules' native fetch pattern.
- Made the default `Complete Sprite Stack` fetch all first-run Sprite needs:
  shared Z-Image INT4 r32 backend, both starter LoRAs, staged ControlNet Union,
  and Depth Anything.
- Extended status and the custom UI to distinguish shared Z-Image backend model
  readiness from Sprite-owned asset readiness.
- Changed the module runner's default generation precision to `int4` so it
  matches the default fetched/loaded Z-Image profile instead of sending `auto`.
- Switched the default selected LoRA to `tarn59_pixel_art`; a one-direction
  smoke test succeeded with it, while the mks0813 file currently trips a
  Nunchaku LoRA tensor-shape mismatch.

## 0.1.15 - 2026-06-05

- Added a Foundry bridge path so the module can call the canonical
  `sprite-foundry` fork flow through `python3 -m foundry.cli generate-nymphscore`.
- Added `foundry_status` and `foundry_generate` module actions, with early
  checks for the local Foundry checkout, selected LoRA path, and Z-Image server.
- Added a `Foundry Run` button to the custom UI that uses the selected imported
  Foundry preset's original `pipeline/chars/*.json` config.
- Extended module status with Foundry availability, root, DB presence, and the
  Foundry generation entrypoint.

## 0.1.14 - 2026-06-05

- Replaced the tiny hand-written prompt preset sample with a generated Sprite
  Foundry character preset catalog from the local `sprite-foundry`
  `pipeline/chars` configs.
- Preserved full Foundry subject prompts, negative prompts, seeds, roles, body
  classes, body locks, reject conditions, pack metadata, and source config
  paths in `profiles/foundry_character_presets.json`.
- Added `profiles/foundry_export_roster.json` from the Foundry export roster so
  the module carries the 92-pack lane/subject target even where prompt configs
  are not yet available.
- Updated the custom UI dropdown to use the generated Foundry preset catalog.
- Aligned direct Z-Image source generation and module-bridge source generation
  with the Foundry NymphsCore runner's style suffix and background-negative
  prompt clause.

## 0.1.13 - 2026-05-30

- Rewired `Generate Sources` to call the Z-Image `/generate` API directly,
  matching Nymphs Image's generation path.
- Kept Manager module actions for module-owned work such as status, folders,
  and Foundry-style post-processing so the UI no longer collides with its own
  status/output refresh actions during image generation.
- Added a queued module-bridge fallback for source generation when local HTML
  cannot call the Z-Image API directly.

## 0.1.12 - 2026-05-30

- Fixed generation from the custom UI by sending prompts, LoRA trigger/path,
  and selected source images through Manager as safe base64url chunks.
- Changed direction selection from comma-separated to `+`-separated for the
  Manager action bridge.

## 0.1.11 - 2026-05-30

- Fixed the custom UI failing to open in WebView2 by replacing the oversized
  inlined forest background data URI with an installed `file://` asset URI.

## 0.1.10 - 2026-05-30

- Replaced the starter prompt presets with Sprite Foundry-derived subjects
  from the character JSON contract.
- Moved `Generate Sources` into the Z-Image section so source generation sits
  before sprite post-processing in the flow.
- Added a module action for loading recent Z-Image outputs into the strip
  picker, so images can be previewed/chosen before processing work.
- Let `Generate + Process` consume checked managed source images instead of
  always regenerating when source images are selected.
- Installed the Nymphs Image forest preview asset and inline it into the
  Manager HTML during install so local HTML can render the same background.

## 0.1.9 - 2026-05-30

- Added a single sprite prompt preset dropdown for module-specific source
  prompts.
- Split the run controls into source image generation and generate-plus-process
  so the Sprite Foundry-style source review step is visible.
- Removed the always-visible raw log from the custom UI stage; logs stay behind
  the strip menu's Logs action.

## 0.1.8 - 2026-05-30

- Removed asset download controls from the custom generation UI.
- Kept asset fetch in the module detail action group, where package download
  and repair choices belong.
- Added a run-level downloaded-LoRA selector for Sprite Foundry-style batch
  setup before source direction generation.
- Restored the Nymphs Image strip organizer shape with a folder picker,
  current preview selection, select-all, and clear-selection controls.

## 0.1.7 - 2026-05-30

- Rebuilt the module-owned UI around the Nymphs Image rail/stage pattern.
- Matched the Nymphs Image sidebar width and mobile collapse breakpoint.
- Added a right-side image preview stage, generated-batch thumbnail strip, and
  contact-sheet/output path detection from generation logs.
- Removed the generic dashboard-card layout and duplicate in-page bottom bar.

## 0.1.6 - 2026-05-30

- Routed the Asset Fetch dropdown through the existing `fetch_lora` capability
  so Manager sessions with stale capability data do not grey out the Fetch
  button.
- Let `nymphs_sprite_fetch_lora.sh` dispatch package, ControlNet, and Depth
  asset choices via `--asset`.

## 0.1.5 - 2026-05-30

- Changed Complete Sprite Package to fetch both starter LoRAs, plus staged
  ControlNet Union and Depth Anything assets.
- Removed the duplicate alternate complete package option.
- Kept `mks0813_pixel_art` selected after a complete fetch until the UI exposes
  LoRA switching.

## 0.1.4 - 2026-05-30

- Replaced separate LoRA, ControlNet, and Depth fetch blocks with one
  module-owned Asset Fetch dropdown.
- Added complete sprite asset package choices for the mks0813 and tarn59 LoRA
  paths, while keeping individual asset choices for repair/testing.
- Trimmed the module action row to reduce Manager detail-page crowding.

## 0.1.3 - 2026-05-30

- Fixed the default `mks0813/z-image-turbo-pixel-art-lora` asset to fetch the
  live `epoch-1.safetensors` file.
- Added standard `MODEL FETCH` progress output for LoRA, ControlNet, and Depth
  fetches.
- Added status fields for downloaded LoRAs, cached sprite assets, ControlNet,
  and Depth readiness so the Manager can show what is local.
- Added module-owned per-LoRA cache deletion through `delete_models`.
