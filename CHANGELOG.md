# Changelog

## 0.1.3 - 2026-05-30

- Fixed the default `mks0813/z-image-turbo-pixel-art-lora` asset to fetch the
  live `epoch-1.safetensors` file.
- Added standard `MODEL FETCH` progress output for LoRA, ControlNet, and Depth
  fetches.
- Added status fields for downloaded LoRAs, cached sprite assets, ControlNet,
  and Depth readiness so the Manager can show what is local.
- Added module-owned per-LoRA cache deletion through `delete_models`.
