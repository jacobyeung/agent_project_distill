# Build brief 14: candidate geometry towers priced on K1 (pose and metric scale)

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. One or two Trinity 48 GB cards for 4 to 12 hours in all, under ORCH's GO; pricing is CPU.

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). GPU: normal priority only on trinity-0-13 (main has priority); elsewhere only under `/data3/shared/scripts/vnice/vnice.sh`; never 0-8, 0-23, 3-23; leave 0-18 free. No Git, no deletion, no download without a governed stream. Lane folder on trinity-1-18 `/scratch/jjyeung/orch_n30/geo_k1`; events `B/events/geo_k1/`.

## Why
E3 (`distill_design/E3_BACKEND_GEOMETRY_PRICING_20261116.md`) showed that no scale or floor rule on G3T makes room programs beat direct answers, that a perfect scale adds at most about 3 task points on metre distance, and that the remaining 12 points to ground-truth geometry are depth shape and pose. Room needs per-capture metric scale within a few percent (GT scale lifts room from 63 to 75 to 77). A tower that is metric by construction or has better pose is the remaining program-side lever, and the same tower feeds GF-1. The bake-off kit exists but prices on ScanNet validation scenes, which are benchmark scenes; under the re-freeze rules a tower may be chosen only on K1.

## Inputs
- Bake-off kit: trinity-1-18 `/scratch/jjyeung/geo_bakeoff_kit` (KIT_SEAL.json, payload with MoGe-2, MapAnything, Depth Anything 3 and Pi3X sources and weights, 65 tests; completeness against the seal unverified: check first) and record `GEOMETRY_BACKEND_BAKEOFF_20261111.md`.
- K1: 300 training captures, frames and tower outputs at trinity-1-18 `/scratch/jjyeung/k1` (`run_tower_sam_2`), 296 GT rasters, split 242 train / 58 held-out by room, manifest v2 (`REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md`).
- E3's harness: trinity-1-18 `/scratch/jjyeung/orch_n30/e3_geom/work/harness` (`run.sh run --gd-dir ROOT` takes one `geometry.npz` per capture and adds an arm; `agg.py` for paired tables; its two unreviewed edits are named in the record: have them reviewed with this work).
- Rules: `REFREEZE_PREREGISTRATION_20261115.md` (C-rule: challenger's paired lower bound above zero on K1 train and point estimate above zero on K1 held-out), the user's rule to reconstruct on dense frames and then subsample.

## What to build
1. A dated pre-registration note (before any candidate's K1 number exists): candidates, the C-rule, primary arms (metre distance with GT masks; room, mask-free), bars (+5 task points on distance over the deployed column; room at least 73.4 on held-out), the reference (the deployed own-scale column once K1's own phase lands, else S4+G1).
2. An adapter per candidate: 64 dense frames in, the tower's exact 32 anchors out, written as `geometry.npz` in the harness's format; each tower run at its own native scale with no fitted scalar.
3. Tower passes on the 300 K1 captures (about 1 to 3 GPU-hours per candidate), resumable per capture.
4. Pricing with the harness, tables on train and held-out, VSI-Bench value as task points divided by 8.

## Decision it changes
Which frozen tower the artifact carries for programs and for GF-1 at the next seal, and whether room has a head path worth training. Ceiling from E3: room +13.3 task points (1.66 VSI points) at oracle scale; distance up to +12 task points with GT masks (1.5 VSI points), less with real masks.

## Tests
Adapter round trip on the kit's 64-frame fixture; the harness reproduces E3's S4+G1 and GT rows before any candidate runs; 65 kit tests; CPU first pass of each tower on one capture.

## Do not touch
`/scratch/jjyeung/k1` contents and the kit copy `kc` (read only), K1's Orchard jobs, D0 job 170111, the VSTI read, any ScanNet validation or benchmark scene.

## Deliver
The note, per-candidate tables, a design record update (`GEOMETRY_BACKEND_BAKEOFF_20261111.md` or a new record) with one INDEX line, mirror on a second node, STATUS.md, RESULT events. Review: one independent reader of the harness edits and the analysis before held-out numbers are read.
