# Subject Sheet — Foundry Phase 1A Test Character

## Character

| Field | Value |
|-------|-------|
| **Name** | Sera Vale |
| **Role** | Crew Broker / Quartermaster |
| **Civilization** | Terran Compact |
| **Game function** | Document expert, manifest auditor, customs navigator |

## Why Sera

Sera is the right mid-complexity test subject:
- Clear professional silhouette (not military, not alien, not ceremonial)
- Enough costume detail to test landmark consistency without chaos
- Asymmetric gear (satchel, data-pad) tests rotation identity
- Human face and practical hair — tests face/hair consistency at the hardest-but-fair level
- Not the easiest (Varek is a big guy with a gun) or the hardest (Thal is alien biology, Ilen is convoy logistics with less visual identity)

## Silhouette Summary

Compact-built woman in a fitted utility vest over a dark undershirt, belted at the waist. Satchel on the left hip, data-pad holstered on the right thigh. Boots to mid-calf. Hair pulled back tight — functional, not decorative.

## Costume Landmarks (7)

1. **Utility vest** — short, fitted, lighter tone than undershirt, visible front pockets
2. **Dark undershirt** — long sleeves rolled to forearm
3. **Wide belt** — visible buckle, divides torso clearly
4. **Left hip satchel** — rectangular, flap closure, strap crosses body
5. **Right thigh data-pad holster** — slim rectangular silhouette on thigh
6. **Mid-calf boots** — practical, slightly chunky sole
7. **Collar or lapel detail** — small rank/ID badge or pin on vest left chest

## Asymmetry Anchors (2)

1. **Satchel on LEFT hip** — always left, never right. This is the primary rotation test: if the satchel switches sides, the direction is wrong.
2. **Data-pad holster on RIGHT thigh** — always right. Secondary rotation anchor.

## Palette Family

| Zone | Color Direction |
|------|-----------------|
| Vest | Muted tan / khaki / warm gray |
| Undershirt | Dark charcoal or navy |
| Belt + boots | Dark brown or near-black |
| Satchel | Warm leather brown, darker than vest |
| Data-pad holster | Same as belt tone |
| Skin | Medium warm tone |
| Hair | Dark brown, pulled back |

Palette is deliberately warm-neutral. No bright accents. The readability comes from value contrast (light vest over dark shirt), not color pop.

## Gear/Tool Silhouette

- **Satchel**: the most visually prominent gear item. Rectangular flap bag, hangs at hip height, strap visible crossing torso in front/back views.
- **Data-pad**: slim rectangle, holstered flat against right thigh. Subtle but must be present in side/diagonal views.
- No weapon. Sera is not a fighter. No holster, no blade, no firearm.

## "Must Stay True" List

These are the hard identity rules. If any of these break across directions, the sprite fails:

1. Satchel is always on the LEFT hip
2. Data-pad holster is always on the RIGHT thigh
3. Vest is lighter than undershirt (value contrast holds)
4. Belt is visible and divides the torso
5. Hair is pulled back (no loose flowing hair in any direction)
6. No weapon visible
7. Boots reach mid-calf
8. Body proportions stay consistent (no direction makes her taller/shorter/wider)

## "Nice to Have" List

These improve quality but are not pass/fail:

1. Satchel strap visible crossing torso in front and back views
2. Rolled sleeves visible in side views
3. Badge/pin on vest visible in front and front-diagonal views
4. Slight lean or weight shift that feels natural
5. Boot sole detail visible in side views

## 8-Direction Turnaround Intent

| Direction | Key Reads |
|-----------|-----------|
| **Front (S)** | Full vest + belt + satchel strap crossing torso. Data-pad holster visible on right thigh. Face visible. |
| **Front-Left (SW)** | Satchel prominent on near hip. Vest pocket visible. Face in 3/4. |
| **Left (W)** | Full satchel profile. Strap line visible. Data-pad hidden behind body. |
| **Back-Left (NW)** | Satchel partially visible. Strap across back. Hair tie/bun visible. |
| **Back (N)** | Strap crossing back. Satchel and data-pad partially hidden by body. Hair detail. No face. |
| **Back-Right (NE)** | Data-pad holster partially visible. Strap across back. |
| **Right (E)** | Full data-pad holster profile. Satchel hidden behind body. |
| **Front-Right (SE)** | Data-pad holster on near thigh. Vest detail. Face in 3/4. |

## Target Output

- **Sprite size:** 48x48 pixels (final gameplay resolution)
- **Generation source:** can be larger, downsampled/pixelated to 48x48
- **Background:** transparent (scene-neutral)
- **Pose:** standing neutral idle (no action pose)
- **Style:** HD-2D-inspired pixel art — deliberate, readable, game-ready

## Anti-Drift Notes

- This is NOT a portrait. It is a gameplay sprite at 48px. Detail must survive at that scale.
- Do NOT add decorative flourishes not in the landmark list.
- Do NOT give her a weapon, hood, cape, or visor.
- Do NOT make the hair loose or flowing.
- Do NOT flip the satchel/data-pad sides.
