## Nymphs Sprite

Nymphs Sprite is a NymphsCore module for guided 8-direction game sprite
generation, review, and export. It uses the evolved Sprite Foundry workflow as a
starting point, then layers on the Nymphs-native path: Nymphs Image / Z-Image
Turbo, Nunchaku acceleration, Z-Image LoRAs, and staged ControlNet/depth-guided
direction control.

The current distillation goal is simple: keep the best of Sprite Foundry's
review, lifecycle, map/finish, and export ideas, but make the everyday flow feel
like a reliable Nymphs sprite-making tool:

```
Character -> Guide -> Style -> Generate -> Review -> Export
```

Huge thanks to the original Sprite Foundry author and MCP Tool Shop for making
the foundation available under MIT.

---

<p align="center">
  <a href="README.ja.md">日本語</a> | <a href="README.zh.md">中文</a> | <a href="README.es.md">Español</a> | <a href="README.fr.md">Français</a> | <a href="README.hi.md">हिन्दी</a> | <a href="README.it.md">Italiano</a> | <a href="README.pt-BR.md">Português (BR)</a>
</p>

<p align="center">
  <img src="ui/nymphs_preview_forest.png" alt="Nymphs Sprite preview" width="600">
</p>

<p align="center">
  <strong>Guided sprite generation for NymphsCore</strong>
</p>

<p align="center">
  <a href="https://github.com/nymphnerds/nymphs-sprite/actions/workflows/ci.yml"><img src="https://github.com/nymphnerds/nymphs-sprite/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="docs/NYMPHS_SPRITE_DISTILLATION_PLAN.md"><img src="https://img.shields.io/badge/docs-distillation_plan-blue" alt="Distillation plan"></a>
</p>

Nymphs Sprite is a local-only asset pipeline that generates, reviews, and exports 8-direction pixel sprites with normal and depth maps. The current source is transplanted from the more evolved Sprite Foundry module, drives Nymphs Image / Z-Image Turbo for generation, uses SQLite for lifecycle tracking, and keeps the Godot finish-lab lighting verification path.

## Architecture

```
Subject Sheet ──► Nymphs Image Generation ──► Mechanical Gates
                  (Z-Image Turbo +           (transparency,
                   Nunchaku + LoRA)           dimensions, count)
                                                │
                                                ▼
                                        Raw/Pixel Review
                                                │
                                                ▼
                                    Normal + Depth Map Gen
                                                │
                                                ▼
                                     Godot Finish Lab
                                     (4 lighting states)
                                                │
                                                ▼
                                      Deterministic Export
                                      (manifest + checksums)
```

## Roster

92 production export packs across 12 lanes:

| Lane | Count | Subjects |
|------|-------|----------|
| Beast | 16 | Bell Warden, Bone Weaver, Clock Golem, Grinning Idol, Hive Keeper, Hollow Knight, Ink Shade, Lantern Angler, Mirror Stalker, Mud Revenant, Rat King, Root Puppet, Spore Mother, Teeth Collector, Throat Singer, Wyvern |
| Townsfolk | 16 | Barmaid, Beggar, Blacksmith, Child, Elder, Farmer, Fisherman, Guard, Herbalist, Innkeeper, Lamplighter, Merchant, Minstrel, Noble, Scribe, Stable Hand |
| Goblin | 8 | Archer, Bomber, Brute, Grunt, Scout, Shaman, Warchief, Wolf Rider |
| Hero | 8 | Barbarian, Cleric, Fighter, Mage, Monk, Paladin, Ranger, Rogue |
| Pirate | 8 | Captain, Cutthroat, Drowned, Governor, Navy Sailor, Pistoleer, Quartermaster, Sea Priest |
| Villain | 8 | Assassin, Blackguard, Cult Priest, Dark Monk, Dread Ranger, Necromancer, Reaver, Warlord |
| Zombie | 8 | Bloater, Elite, Hazmat, Riot, Runner, Shambler, Skeletal, Worker |
| Creature | 6 | Cargo Beast, Drift Maw, Skitter Drone, Drift Lurker, Void Raptor, Keth Healer-Drone |
| Crew | 7 | Sera Vale, Ilen Marr, Thal, Thal (Hazard Suit), Varek, Kael Morrow, Hull Diver |
| Hostile | 3 | Scav Raider, Reach Pirate, Compact Interdiction Agent |
| Authority | 2 | Compact Patrol Officer, Veshan House Envoy |
| Civilian | 2 | Nera Quill, Orryn Broker |

## Monster Lane

Non-humanoid creatures use body-class-specific depth guides in the original ComfyUI path. This fork keeps those configs and review gates while the NymphsCore backend grows toward Z-Image ControlNet/depth parity.

| Body Class | Depth Strength | End % | Creatures |
|------------|---------------|-------|-----------|
| Amorphous | 0.35 | 65% | Rat King, Spore Mother, Mud Revenant |
| Wide/Squat | 0.40 | 70% | Grinning Idol |
| Tall/Thin | 0.40 | 70% | Lantern Angler, Root Puppet |

Depth guides are joint-free primitives (blobs, pillars, columns) that lock in mass and orientation without dictating skeleton or limb placement. The `body_class` field in character configs auto-selects the correct preset:

```bash
# Original ComfyUI body class path
python -m pipeline.foundry_gen_morph --config pipeline/chars/beast_rat_king.json

# CLI override
python -m pipeline.foundry_gen_morph --config pipeline/chars/beast_rat_king.json --body-class tall_thin
```

## Export Contract v1.0.0 (frozen)

```
exports/{subject_slug}/{run_id}/
├── albedo/    8 × transparent PNGs
├── normal/    8 × matching normal maps
├── depth/     8 × matching depth maps
├── preview/   contact sheet
└── manifest.json  (schema v1.0.0, SHA-256 checksums, provenance)
```

- 8 directions: front, front_left, left, back_left, back, back_right, right, front_right
- Original contract: 48×48 transparent PNG, center_bottom pivot
- NymphsCore fork: configurable `--sprite-size` from 24 to 512, default 96
- Consumers validate `schema_version: "1.0.0"` before loading

## Prerequisites

- Python 3.11+
- Nymphs Image running locally, usually at `http://127.0.0.1:8090`
- Z-Image Turbo model with Nunchaku runtime support
- A Z-Image Turbo-compatible sprite/pixel-art LoRA
- ComfyUI is optional legacy/reference runtime for the original generation scripts
- Godot 4.6 (for finish lab rendering)
- NVIDIA GPU recommended

## Quick Start

```bash
# Clone
git clone https://github.com/nymphnerds/nymphs-sprite.git
cd nymphs-sprite

# Initialize the registry
python -m foundry init

# Register a subject
python -m foundry subject-add sera_vale "Sera Vale" --role crew --consumer star-freight

# Check the full pipeline status
python -m foundry status

# Generate through Nymphs Image / Z-Image Turbo
python -m foundry.cli generate-nymphscore \
  --config pipeline/chars/thal.json \
  --nymphscore-url http://127.0.0.1:8090 \
  --sprite-size 96
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize the foundry SQLite registry |
| `subject-add` | Register a new character subject |
| `generate-nymphscore` | Generate and register a run through Nymphs Image / Z-Image Turbo |
| `register-run` | Record a generation run |
| `register-attempt` | Record an individual attempt within a run |
| `check` | Run mechanical validation gates |
| `review-show` | Display review queue for a run |
| `review-accept` | Accept an attempt at current review stage |
| `review-reject` | Reject an attempt with a reject code |
| `batch-accept` | Accept all pending attempts in a run |
| `batch-reject` | Reject all pending in a run with one code |
| `regen` | Queue regeneration for rejected attempts |
| `attempt-detail` | Show full lifecycle for one attempt |
| `finish-board` | Generate a finish-lab comparison board |
| `status` | Pipeline status summary |
| `story` | Full provenance narrative for a subject |
| `lineage` | Regen chain for an attempt |
| `winner` | Canonical winner per direction |
| `drift` | Failure pattern analysis and pass rates |
| `metrics` | Throughput metrics (per-run or foundry-wide) |
| `produce` | One-command: maps + finish captures for an accepted run |
| `export` | Export a finish-accepted run as a deterministic asset pack |

## Threat Model

Nymphs Sprite is a **local developer tool**. It does not:

- Access external services by default; generation calls local Nymphs Image on localhost
- Handle secrets, tokens, or credentials
- Collect or send telemetry
- Write outside its own working directory

File operations are constrained to `exports/`, `bakeoff/`, `boards/`, `derived/`, and the SQLite registry. Subprocess calls are limited to local generation APIs and Godot headless rendering.

## License

[MIT](LICENSE)

---

<p align="center">
  Built by <a href="https://mcp-tool-shop.github.io/">MCP Tool Shop</a>
</p>
