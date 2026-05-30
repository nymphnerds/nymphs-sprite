# Changelog

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
