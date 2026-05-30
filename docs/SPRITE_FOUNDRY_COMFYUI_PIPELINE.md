# Sprite Foundry ComfyUI Pipeline

This note extracts the ComfyUI execution layer used by upstream
`mcp-tool-shop-org/sprite-foundry`. The upstream Python code builds these graphs
in code and sends them to ComfyUI's API. The templates in
`../comfyui_workflows/` make those graphs explicit.

For Nymphs Sprite, these are reference graphs only. The active generation target
is Z-Image Turbo through Nymphs Image with a Z-Image Turbo-compatible LoRA.

The useful split for NymphsCore is:

```text
Sprite Foundry orchestration: registry, attempts, gates, reviews, export
ComfyUI execution layer: image generation, morphology control, normal/depth maps
```

If NymphsCore becomes the execution layer, these JSON files are the behavior to
match or replace.

## Nymphs Sprite Target

Generation should call the existing Nymphs Image API instead of recreating
ComfyUI's SDXL stack:

```text
POST http://127.0.0.1:8090/generate
```

Request template:

```text
profiles/zimage_turbo_sprite_request.json
```

Key fields:

```text
provider:           zimage
mode:               txt2img
model_id:           Tongyi-MAI/Z-Image-Turbo
nunchaku_precision: auto
nunchaku_rank:      32
lora_path:          __Z_IMAGE_TURBO_LORA_PATH__
lora_scale:         0.85
```

The LoRA must be trained for Z-Image Turbo. The upstream SDXL LoRA field
`pixel-art-xl.safetensors` is not compatible with this path.

The relevant Nymphs Image source already supports this:

```text
scripts/_zimage_common.sh sets ZIMAGE_LORA_ROOT
api_server.py GET /api/loras lists available LoRAs
api_server.py POST /generate accepts lora_path and lora_scale
model_manager.py applies the LoRA to the Z-Image pipeline
```

Nymphs Sprite's runner should be a client of those paths, not a second LoRA
loader.

## API Shape

Upstream posts workflow JSON to:

```text
POST http://127.0.0.1:8188/prompt
GET  http://127.0.0.1:8188/history/{prompt_id}
GET  http://127.0.0.1:8188/view?filename=...&subfolder=...&type=output
POST http://127.0.0.1:8188/upload/image
```

The files here use ComfyUI API prompt JSON, not the visual editor export format.
They are meant for code-driven submission.

## Upstream Reference Workflows

### Base 8-Direction Generation

Template:

```text
comfyui_workflows/sprite_foundry_base_generation_api.json
```

Nodes:

```text
CheckpointLoaderSimple
LoraLoader
CLIPTextEncode positive
CLIPTextEncode negative
EmptyLatentImage
KSampler
VAEDecode
SaveImage
```

Upstream model assumptions:

```text
checkpoint: juggernautXL_ragnarokBy.safetensors
lora:       pixel-art-xl.safetensors
size:       576x768
steps:      30
cfg:        7.5
sampler:    euler_ancestral
scheduler:  normal
```

Positive prompt shape:

```text
{subject_prompt}, {direction_prompt}, pixel art sprite, game character sprite,
2D RPG, clean pixel art, bright green background, #00FF00 green screen
background, centered composition, full body shot, character centered in frame,
HD-2D inspired, crisp pixel edges, single character portrait, character design,
isolated figure
```

Negative prompt appends:

```text
white background, gray background, grey background, beige background,
gradient background
```

The upstream runner then performs chroma-key or corner-color cleanup, square
crop, 48x48 nearest-neighbor pixelation, contact sheet generation, and foundry
DB registration outside ComfyUI.

In Nymphs Sprite, the analogous generation stage should produce full-size
Z-Image Turbo outputs first, then run the same cleanup, square crop, 48x48
nearest-neighbor pixelation, contact sheet generation, and DB registration.

### Morphology-Controlled Generation

Templates:

```text
comfyui_workflows/sprite_foundry_morph_depth_api.json
comfyui_workflows/sprite_foundry_morph_depth_canny_api.json
```

Additional nodes:

```text
ControlNetLoader
LoadImage
ControlNetApplyAdvanced
```

Depth model:

```text
controlnet-depth-sdxl-1.0.safetensors
```

Optional edge model:

```text
controlnet-canny-sdxl-1.0.safetensors
```

Body-class presets from upstream:

| Body class | Depth refs | Depth strength | Depth end | Canny |
| --- | --- | ---: | ---: | --- |
| arthropod | skitter_drone_depth | 0.55 | 0.80 | no |
| quadruped | cargo_beast_depth | 0.65 | 0.90 | no |
| crouching_predator | drift_lurker_depth | 0.55 | 0.80 | no |
| winged | void_raptor_depth | 0.55 | 0.90 | yes |
| amorphous | amorphous_depth | 0.35 | 0.65 | no |
| wide_squat | wide_squat_depth | 0.40 | 0.70 | no |
| tall_thin | tall_thin_depth | 0.40 | 0.70 | no |

Each direction needs a matching uploaded reference image, for example:

```text
front_depth_ref.png
front_left_depth_ref.png
left_depth_ref.png
back_left_depth_ref.png
back_depth_ref.png
back_right_depth_ref.png
right_depth_ref.png
front_right_depth_ref.png
```

The Canny/edge variant also expects:

```text
front_edge_ref.png
...
front_right_edge_ref.png
```

### Normal And Depth Maps

Templates:

```text
comfyui_workflows/sprite_foundry_normal_map_api.json
comfyui_workflows/sprite_foundry_depth_map_api.json
```

Normal map node:

```text
MiDaS-NormalMapPreprocessor
```

Depth map node:

```text
DepthAnythingPreprocessor
```

Depth checkpoint:

```text
depth_anything_vitl14.pth
```

The upstream runner uploads the accepted raw sprite image, runs both workflows,
then crops/pixelates each returned map to 48x48 and registers both raw and
pixelated map artifacts.

## Direction Prompts

Upstream uses exactly these eight directions:

| Direction | Prompt |
| --- | --- |
| front | facing the viewer, front view, looking at camera |
| front_left | facing front-left, 3/4 view from the left, looking slightly left |
| left | facing left, left side profile view |
| back_left | facing back-left, 3/4 rear view from the left |
| back | facing away from viewer, rear view, back of character |
| back_right | facing back-right, 3/4 rear view from the right |
| right | facing right, right side profile view |
| front_right | facing front-right, 3/4 view from the right, looking slightly right |

## NymphsCore Replacement Targets

To make this Nymphs-native, replace the ComfyUI graph calls with module-owned
NymphsCore stages:

| Upstream ComfyUI stage | NymphsCore equivalent |
| --- | --- |
| SDXL checkpoint + pixel LoRA generation | Nymphs Image Z-Image Turbo request with Z-Image LoRA |
| ControlNet depth/canny morphology | Nymphs morphology guide runner or guided image provider |
| ComfyUI upload/image | NymphsData staged input artifact |
| ComfyUI history polling | Nymphs module job/progress state |
| SaveImage output | NymphsData output registration |
| MiDaS normal map preprocessor | local normal-map derivation stage |
| DepthAnything preprocessor | local depth-map derivation stage |

The Foundry DB, review boards, mechanical gates, and deterministic export
contract can stay almost intact once generation produces the same artifact kinds:

```text
raw
pixel
normal_raw
normal
depth_raw
depth
contact_sheet
raw_inspection
```
