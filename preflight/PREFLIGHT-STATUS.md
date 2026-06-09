# Phase 1A.0 Preflight — Status

## Artifact Status

| # | Artifact | Status | Location |
|---|----------|--------|----------|
| 1 | Subject Sheet | **DONE** | `preflight/subject-sheet.md` |
| 2 | ComfyUI Inventory | **DONE — blockers resolved** | `preflight/comfyui-inventory.md` |
| 3 | Godot Render-Lab Skeleton | **DONE** | `preflight/godot-render-lab.md` + `game/godot/render-lab/` |
| 4 | Placeholder Contact Sheet | **DONE** | `preflight/contact-sheet-placeholder.png` |

## Preflight Checklist

- [x] Subject definition sheet locked (Sera Vale — mid-complexity crew broker)
- [x] 48x48 sprite size locked
- [x] Local ComfyUI inventory recorded (9 checkpoints, 9 LoRAs, 7 ControlNets, 7 IP-Adapters, 3 upscalers)
- [x] 3 candidate stack archetypes viable (all blockers resolved)
- [x] Godot 4.6.1 installed + render-lab skeleton created
- [x] Contact-sheet PNG generation working with placeholders

## Blockers — ALL RESOLVED

| # | Blocker | Resolution |
|---|---------|------------|
| ~~1~~ | ~~No pixel-art LoRA~~ | **RESOLVED** — pixel-art-xl.safetensors + PixelArtRedmond-Lite64.safetensors downloaded |
| ~~2~~ | ~~No comfyui_controlnet_aux~~ | **RESOLVED** — cloned + deps installed |
| ~~3~~ | ~~No pixelation node/script~~ | **RESOLVED** — `pipeline/pixelate.py` (Pillow nearest-neighbor, palette reduction) |
| ~~4~~ | ~~Godot 4 not installed~~ | **RESOLVED** — Godot 4.6.1 at `F:\AI\Godot\` |

## Stack Viability

| Stack | Shape | Viable? |
|-------|-------|---------|
| A — Pixel-Native | JuggernautXL + pixel-art-xl LoRA (high weight) | **YES** |
| B — Stylized + Cleanup | JuggernautXL + PixelArtRedmond LoRA + pixelate.py | **YES** |
| C — Reference Control | JuggernautXL + IP-Adapter + ControlNet + pixel LoRA | **YES** |

### Nice to Have (Not Blocking)

| # | Item | Fix |
|---|------|-----|
| 5 | CLIP-ViT-bigG incomplete download | Re-download (ViT-H is sufficient for now) |
| 6 | No ComfyUI-Manager | Install later for convenience |
| 7 | No SDXL tile ControlNet | canny+depth+pose is sufficient |

## PREFLIGHT COMPLETE

All four artifacts exist. All blockers resolved. All three stack archetypes are viable.

**Next step:** Pass A bakeoff — albedo-only generation of Sera Vale across 8 directions using all 3 stacks.
