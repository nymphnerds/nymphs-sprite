# Subject Sheet — Scav Raider

## Identity
- **Name:** Scav Raider (generic hostile, not unique NPC)
- **Asset class:** enemy
- **Civilization:** Unaffiliated (fringe raiders, ex-Terran deserters)
- **Role:** Melee/close-range pirate combatant. The most common hostile encounter in Star Freight.
- **Silhouette class:** Humanoid hostile — similar proportions to crew characters but rougher, bulkier, more threatening

## Visual Design

### Body
- Human-proportioned, slightly hunched aggressive posture
- Medium-heavy build, not athletic — scrappy and dangerous
- Covered face — balaclava or welding mask, no exposed face (enemies are anonymous)
- Dark, dirty palette: charcoal, rust brown, dull orange accents

### Costume Landmarks (asymmetry anchors)
1. **RIGHT arm — improvised blade gauntlet** (pipe + welded blade on forearm, most prominent feature)
2. **LEFT shoulder — scavenged metal plate** (irregular shape, bolted on, scratched)
3. **Chest — salvaged EVA vest** (torn, patched, utility loops, dark grey-brown)

### Distinguishing Features
- Heavy utility belt with salvage pouches
- Knee-high reinforced boots (mismatched, one darker than other)
- Cable/wire wrapped around left forearm under the shoulder plate
- Aggressive forward-leaning stance (not military upright)

### Color Palette
- Primary: charcoal, dark grey-brown
- Secondary: rust/oxidized orange (blade, shoulder plate edges)
- Accent: dull yellow-green on utility belt clips

### 8-Direction Notes
- Front: blade gauntlet on right arm prominent, shoulder plate on left, masked face
- Side: hunched silhouette, blade extending past hand line
- Back: shoulder plate visible on left, vest straps crossing back, belt pouches

## Readability at 48px
- Blade gauntlet is the silhouette key — must extend past hand line in all views
- Shoulder plate must read as asymmetric mass on left side
- Masked face + hunched posture = "hostile" read distinct from upright crew characters
- Dark palette means background removal tolerance may need attention

## Pipeline Notes
- Asset class: enemy (first enemy in foundry)
- Same 8-direction pipeline as characters
- Same mechanical gates should apply
- Watch for: dark palette causing corner_transparency gate issues, hunched posture affecting center-crop
