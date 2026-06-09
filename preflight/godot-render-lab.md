# Godot Render-Lab Skeleton — Phase 1A Preflight

## Status: READY

Godot 4.6.1 installed at `F:\AI\Godot\Godot_v4.6.1-stable_win64.exe`
Render-lab project created at `F:\AI\star-freight-foundry\game\godot\render-lab\`

### Render-Lab Project Skeleton (Ready to Create)

Once Godot is installed, create project at `F:\AI\star-freight-foundry\game\godot\render-lab\`:

```
render-lab/
  project.godot
  assets/
    sprites/          # accepted 48x48 albedo PNGs
    normals/          # matching normal maps
    depth/            # matching depth maps
  scenes/
    render_lab.tscn   # main lab scene
  scripts/
    lab_controls.gd   # light/shader/particle toggle
    screenshot.gd     # capture to file
  screenshots/        # output captures
```

### Proof Checklist (Must Pass Before Preflight Complete)

- [ ] Godot 4 installed and opens
- [ ] Render-lab project created and opens without errors
- [ ] One placeholder sprite (48x48 PNG) imports cleanly
- [ ] One normal map texture loads and attaches via CanvasTexture
- [ ] One Light2D node affects the sprite visibly
- [ ] One CanvasItem shader compiles (even trivial: modulate color)
- [ ] Screenshot saves to disk from script or editor

### Minimal Lab Scene Design

```
render_lab.tscn
├── Node2D (root)
│   ├── Camera2D
│   ├── GroundPlane (ColorRect or Sprite2D — neutral dark)
│   ├── CharacterSprite (Sprite2D + CanvasTexture)
│   │   └── material: CanvasTexture(diffuse, normal, specular)
│   ├── LightRigA (PointLight2D — warm dusk torch)
│   ├── LightRigB (PointLight2D — cold moonlight)
│   ├── Particles_Ember (GPUParticles2D)
│   ├── Particles_Dust (GPUParticles2D)
│   └── ScreenshotCapture (Node + screenshot.gd)
```

### Lab Controls (lab_controls.gd)

Simple keyboard toggles:
- `1` / `2` — switch light rig A / B
- `P` — toggle particles on/off
- `S` — toggle shader preset A / B
- `0` — no-finish baseline (all lights/shaders/particles off, flat sprite)
- `F12` — capture screenshot

### Light Rig Specs

**Rig A — Dusk Torch:**
- PointLight2D, warm orange (#FF9944), energy 1.2, height 80
- Position: slightly above and to the right of character

**Rig B — Cold Moonlight:**
- PointLight2D, cool blue-white (#AACCFF), energy 0.8, height 120
- Position: above and behind character (higher, more diffuse)

### Shader Presets

**Preset A — Soft Rimlight:**
- CanvasItem shader that adds a subtle bright edge based on normal map Z values
- Low intensity — enhancement, not glow

**Preset B — Atmospheric Depth:**
- Mild color shift based on a depth/distance value
- Slightly desaturates and blues distant elements

### This Is Not a Game Build

The render lab exists only to answer: "Does the runtime finish make the assets feel premium?"

No combat. No inventory. No navigation. No UI beyond toggle keys.
