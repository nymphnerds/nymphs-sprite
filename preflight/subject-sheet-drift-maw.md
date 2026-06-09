# Subject Sheet — Drift Maw

## Identity
- **Name:** Drift Maw (alien predator)
- **Asset class:** enemy
- **Civilization:** None (wild fauna, deep-space predator)
- **Role:** Ambush predator encountered in derelict ships and abandoned stations. Dangerous non-humanoid threat.
- **Silhouette class:** Non-humanoid hostile — quadrupedal/crouched, wide horizontal body plan. Hardest pipeline pressure test.

## Visual Design

### Body
- Low-slung quadrupedal predator, like a deep-sea anglerfish crossed with a lizard
- Wide, flat body — wider than tall at 48px
- Four thick legs splayed outward, low to ground
- Long jaw/mouth is the dominant feature — oversized hinged mandible
- Smooth dark carapace with bioluminescent seam lines
- No upright posture — entirely horizontal body plan

### Costume Landmarks (asymmetry anchors)
1. **HEAD — oversized jaw/mandible** (open or half-open, showing teeth, extends forward past body line)
2. **LEFT flank — bioluminescent patch** (pale blue-green glow seam, most visible from left/front-left)
3. **TAIL — segmented armored tail** (curves right, shorter than body length, barbed tip)

### Distinguishing Features
- Compound eyes (4 small eyes in a cluster, faintly glowing amber)
- Dorsal ridge of small spines along back center
- Underbelly lighter than carapace (dark charcoal top, grey-brown belly)
- Legs end in three-toed splayed feet with visible claws

### Color Palette
- Primary: dark charcoal-black carapace
- Secondary: grey-brown underbelly
- Accent: pale blue-green bioluminescent seam (left flank + jaw edges)
- Eyes: amber-orange glow (tiny but readable)

### 8-Direction Notes
- Front: wide jaw dominant, eyes visible, low flat silhouette, legs splayed
- Side: long horizontal profile, jaw extends forward, tail curves back
- Back: dorsal spines, tail visible, carapace dome shape
- The horizontal body plan means this creature is WIDER than characters — may need different crop logic

## Readability at 48px
- Jaw/mandible is the silhouette key — must be the largest and most readable feature
- Bioluminescent seam provides color accent that aids dark-on-dark readability
- Low horizontal profile means the center-crop may cut poorly — the creature fills width, not height
- At 48px, the four legs may merge — accept this if the jaw and body mass read clearly

## Pipeline Notes
- Asset class: enemy (second enemy, first non-humanoid)
- **THIS IS THE KEY PRESSURE TEST** — the pipeline assumes portrait-aspect generation (576x768) and center-crop for square. A horizontal creature in portrait framing will have wasted vertical space.
- The `pixelate_map` center-crop (`top = (h - w) // 4`) may cut legs or tail
- The `foreground_content` gate should still pass if the creature has enough opaque pixels
- The `single_subject` gate may need attention — a wide low creature might not trigger "center-dominant"
- Consider: if portrait aspect fails badly, this proves the pipeline needs asset-class-specific generation parameters
- Same finish rig should work — moonlight on bioluminescence could look excellent
