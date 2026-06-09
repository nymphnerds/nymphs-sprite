# ComfyUI Inventory — Phase 1A Preflight

Runtime: `F:\AI-Models\ComfyUI-runtime`
Models: `F:\AI-Models\ComfyUI\models` (via `extra_model_paths.yaml`)

## Checkpoints

| Model | Architecture | Pixel Art Viability | Tag |
|-------|-------------|--------------------|----|
| dreamshaper_8.safetensors | SD 1.5 | Stylized/fantasy, needs pixel LoRA | maybe |
| epicrealismNaturalSinRC1VAE.safetensors | SD 1.5 | Photorealistic — wrong domain | irrelevant |
| flux1-schnell.safetensors | Flux | Fast gen, no pixel specialization, limited LoRA ecosystem | maybe |
| juggernautXL_ragnarokBy.safetensors | SDXL | Strong character detail, good base for cleanup pipeline | **usable** |
| juggernautXL_v9Rundiffusionphoto2.safetensors | SDXL | Photo-focused variant | maybe |
| leosamsHelloworldXL_helloworldXL70.safetensors | SDXL | General purpose SDXL | maybe |
| realisticVisionV60B1_v60B1VAE.safetensors | SD 1.5 | Photorealistic — wrong domain | irrelevant |
| realvisxlV50_v50Bakedvae.safetensors | SDXL | Photo-leaning | irrelevant |
| realvisxlV50_v50LightningBakedvae.safetensors | SDXL | Fast photo — wrong domain | irrelevant |

**Summary:** No pixel-art-native checkpoint installed. Best available base for character work is JuggernautXL (strong anatomy/costume detail). DreamShaper is the SD1.5 fallback with more stylized range.

## LoRAs

| Model | Architecture | Purpose | Tag |
|-------|-------------|---------|-----|
| DetailTweakerXL.safetensors | SDXL | Detail enhancement | **usable** |
| IconsRedmondV2-Icons.safetensors | SDXL | Icon generation — wrong domain | irrelevant |
| LogoRedmondV2-Logo-LogoRedmAF.safetensors | SDXL | Logo generation — wrong domain | irrelevant |
| add_detail.safetensors | SD 1.5 | Detail enhancement | maybe |
| epiNoiseoffset_v2.safetensors | SD 1.5 | Contrast/lighting control | maybe |
| logomkrdsxl.safetensors | SDXL | Logo — wrong domain | irrelevant |
| skin_texture_xl.safetensors | SDXL | Skin texture — photo domain | irrelevant |

**Summary:** No pixel-art LoRA installed. DetailTweakerXL is useful for sharpening. **BLOCKER: need at least one pixel-art LoRA for Stack A.**

## ControlNet Models

| Model | Architecture | Purpose | Tag |
|-------|-------------|---------|-----|
| control_v11f1e_sd15_tile.safetensors | SD 1.5 | Tile/detail preservation | **usable** |
| control_v11f1p_sd15_depth.safetensors | SD 1.5 | Depth conditioning | **usable** |
| control_v11p_sd15_canny.safetensors | SD 1.5 | Edge conditioning | **usable** |
| control_v11p_sd15_openpose.safetensors | SD 1.5 | Pose conditioning | **usable** |
| controlnet-canny-sdxl-1.0.safetensors | SDXL | Edge conditioning | **usable** |
| controlnet-depth-sdxl-1.0.safetensors | SDXL | Depth conditioning | **usable** |
| controlnet-openpose-sdxl.safetensors | SDXL | Pose conditioning | **usable** |

**Summary:** Good ControlNet coverage for both SD1.5 and SDXL. Pose + Depth + Canny available for rotation control. No tile ControlNet for SDXL (only SD1.5).

## IP-Adapter Models

| Model | Architecture | Purpose | Tag |
|-------|-------------|---------|-----|
| ip-adapter_sd15.safetensors | SD 1.5 | Image reference conditioning | **usable** |
| ip-adapter-plus_sd15.safetensors | SD 1.5 | Stronger image reference | **usable** |
| ip-adapter-faceid_sd15.bin | SD 1.5 | Face identity preservation | **usable** |
| ip-adapter_sdxl_vit-h.safetensors | SDXL | Image reference conditioning | **usable** |
| ip-adapter-plus_sdxl_vit-h.safetensors | SDXL | Stronger image reference | **usable** |
| ip-adapter-faceid_sdxl.bin | SDXL | Face identity preservation | **usable** |

**Summary:** Full IP-Adapter suite for both architectures. FaceID variants available. This is strong for Stack C (reference-heavy control).

## CLIP Vision

| Model | Tag |
|-------|-----|
| CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors | **usable** (required for IP-Adapter) |
| CLIP-ViT-bigG-14-laion2B-39B-b160k.safetensors.tmp | incomplete download — **missing** |

## Upscale Models

| Model | Purpose | Tag |
|-------|---------|-----|
| 4xUltrasharp_4xUltrasharpV10.pt | 4x detail upscale | **usable** |
| RealESRGAN_x4plus.pth | 4x general upscale | **usable** |
| RealESRGAN_x4plus_anime_6B.pth | 4x anime-style upscale | **usable** |

**Summary:** Good upscale coverage. RealESRGAN_anime may work best for stylized sprites before pixelation.

## VAE

| Model | Tag |
|-------|-----|
| sdxl_vae.safetensors | **usable** |
| hunyuan_video_vae_bf16.safetensors | video — irrelevant |

## Text Encoders / CLIP

| Model | Tag |
|-------|-----|
| clip_l.safetensors | **usable** |
| t5xxl_fp16.safetensors | **usable** (Flux) |
| clip-vit-large-patch14/ | **usable** |

## Embeddings

| Model | Tag |
|-------|-----|
| bad-hands-5.pt | **usable** (negative embedding) |

## Custom Nodes

| Node | Tag |
|------|-----|
| example_node.py.example | placeholder only |
| websocket_image_save.py | **usable** (headless output) |

**Summary:** No comfyui_controlnet_aux installed. No pixelation nodes. No custom workflow nodes. **BLOCKER: need controlnet_aux for map derivation (normals, depth via MiDaS/BAE).**

---

## Stack Archetype Assessment

### Stack A — Pixel-Native
**Status: BLOCKED**
- No pixel-art checkpoint or LoRA installed
- No pixelation/downscale nodes installed
- **Shopping list:** 1 pixel-art SDXL LoRA (e.g. Pixel Art XL), 1 pixelation node pack

### Stack B — Stylized Character + Controlled Cleanup
**Status: PARTIALLY READY**
- JuggernautXL as base checkpoint: strong character/costume detail
- DetailTweakerXL for sharpening
- Upscale models available for generate-large-then-downscale pipeline
- **Shopping list:** 1 pixel-art LoRA to blend, pixelation node or script

### Stack C — Reference-Heavy Control
**Status: PARTIALLY READY**
- Full IP-Adapter suite (SD1.5 + SDXL, including FaceID)
- ControlNet pose + depth + canny for both architectures
- CLIP-ViT-H available for reference conditioning
- **Shopping list:** same pixel LoRA + pixelation needs as Stack B, possibly comfyui_controlnet_aux for combined conditioning

---

## Blockers (Must Resolve Before Bakeoff)

| # | Blocker | Impact | Fix |
|---|---------|--------|-----|
| 1 | **No pixel-art LoRA** | Cannot produce pixel-style output from any stack | Download 1-2 pixel art LoRAs (SDXL priority) |
| 2 | **No comfyui_controlnet_aux** | Cannot derive normal/depth maps from sprites | Install controlnet_aux custom node package |
| 3 | **No pixelation nodes** | Cannot enforce crisp pixel grid in ComfyUI | Install pixelation node pack OR use external script |
| 4 | **CLIP-ViT-bigG incomplete** | May limit some IP-Adapter configs | Re-download or verify ViT-H is sufficient |
| 5 | **No custom workflow nodes** | Headless automation limited | Install ComfyUI-Manager or build minimal controller |

## Non-Blockers (Can Work Around)

- No pixel-art checkpoint: JuggernautXL + pixel LoRA + cleanup is a valid approach
- No SDXL tile ControlNet: canny + depth + pose is sufficient for rotation control
- Limited embeddings: bad-hands-5 is the main one needed; can add more later
- Pixelation can be done as a Python post-process step (Pillow nearest-neighbor downscale) if no ComfyUI node is preferred
