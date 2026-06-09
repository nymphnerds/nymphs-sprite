# Canon Batch 02 — Star Freight Production

**Baseline:** v0.1.0-foundry-baseline (10 subjects, 88 finish-accepted, 352 captures)
**Date:** 2026-03-26

## Batch Order

Run in this order. Easiest proven lanes first, creature last.

| # | Subject | Config | Stack | Lane | Priority |
|---|---------|--------|-------|------|----------|
| 1 | Sera Vale (Compact Broker) | `sera.json` | A_v2 | Bipedal crew | Proven — run first |
| 2 | Nera Quill (Compact Face) | `nera.json` | A_v2 | Bipedal crew | Proven |
| 3 | Compact Patrol Officer | `compact_patrol.json` | A_v2 | Bipedal authority | Proven |
| 4 | Reach Pirate | `reach_pirate.json` | A_v2 | Bipedal hostile | Proven |
| 5 | Orryn Broker (civilian) | `orryn_broker.json` | A_v2 | Bipedal civilian | Proven — readability floor test |
| 6 | Keth Healer-Drone | `keth_healer_drone.json` | A_v2_morph (Depth) | Arthropod creature | Proven lane — needs depth refs |

## Commands per subject (bipedal — subjects 1-5)

```bash
# Register
python -m foundry.cli subject-add <id> --name "<Display Name>"

# Generate (ComfyUI must be running)
python -m pipeline.foundry_gen --config pipeline/chars/<config>.json

# Review + accept
python -m foundry.cli batch-accept <run_id> --stage raw
python -m foundry.cli batch-accept <run_id> --stage pixel

# Produce (maps + Godot finish)
python -m foundry.cli produce <run_id>

# Finish review
python -m foundry.cli finish-board <run_id>
python -m foundry.cli batch-accept <run_id> --stage finish
```

## Commands for subject 6 (Keth Healer-Drone — arthropod)

```bash
# Generate depth refs first (new creature — needs custom morph ref)
# Create pipeline/morph_refs/keth_healer_drone_depth/ with 8-direction silhouettes

# Register
python -m foundry.cli subject-add keth_healer_drone --name "Keth Healer-Drone"

# Generate with morphology control
python -m pipeline.foundry_gen_morph \
  --config pipeline/chars/keth_healer_drone.json \
  --depth-refs pipeline/morph_refs/keth_healer_drone_depth

# Then same review/produce/finish flow as bipedal
```

## Design Notes

- **Sera vs Nera:** Both Compact, but Sera is cargo-law street smart (satchel, badge, professional coat). Nera is institutional power (spectacles, folio, seal pendant, austere tunic). Silhouettes must be distinguishable at sprite scale.
- **Reach Pirate vs Scav Raider:** Scav is desperate and scrappy (balaclava, welded blade gauntlet). Reach Pirate is calm and factional (duster coat, gorget trophy, faction tag). Different threat grammar.
- **Compact Patrol:** First authority figure. Clean military uniform reads as "law" at distance — contrast against both pirate types.
- **Orryn Broker:** Lightest silhouette in the set. Loose robe, no gear, alien skin tone. Readability floor — if this reads clearly at sprite scale, the pipeline handles civilians.
- **Keth Healer-Drone:** Non-combat arthropod. Warm amber glow, rounded body, medical manipulators. Proves the arthropod lane works for non-threatening creatures too.

## Review Verdict — 2026-03-26

All 5 new subjects **APPROVED**. Zero regens.

| # | Subject | Verdict | Notes |
|---|---------|---------|-------|
| 1 | Sera Vale | Accept | Done in Batch 01 (stack_a_v2 run) |
| 2 | Nera Quill | Accept | Institutional silhouette clean, no drift |
| 3 | Compact Patrol Officer | Accept | Strongest read in the set — law silhouette holds |
| 4 | Reach Pirate | Accept | Distinct from Scav Raider — calm factional threat |
| 5 | Orryn Broker | Accept | Teal robe + pale skin = immediate civilian read |
| 6 | Keth Healer-Drone | Accept (soft note) | Body plan reads well. Medical manipulator detail is below 48px readability ceiling — role-specific function not legible at base resolution, but class read is good enough for production |

**Batch totals:** 40/40 finish-accepted, 160 captures, 0 rejects.

## R&D (separate — do NOT mix into this batch)

Wing pose locking stays on its own branch. Phase 5C research does not contaminate content production.
