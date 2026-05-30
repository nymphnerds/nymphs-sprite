# Changelog

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
