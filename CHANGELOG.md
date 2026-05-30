# Changelog

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
