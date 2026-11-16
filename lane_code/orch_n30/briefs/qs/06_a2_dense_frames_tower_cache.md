# Build brief 06: dense frames, tower cache and the registration card for the A2 leg (A0 plus GF-1)

Builder: Claude Opus, high effort. Written by lane queue_synth, 2026-11-16. Deadline: A2 can start when D0 ends (D0's step 1,000 is due about 2026-11-18T02:00Z if its second allocation runs).

## Rules
Read `/home/jjyeung/.claude/CLAUDE.md` section "Key Trinity Cluster Rules", then `B/tools/CLAUDE_LANE_RULES.md` and `B/tools/LANE_RULES.md` (B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`). No Git, no deletion, no GPU, no Orchard job without an ORCH GO naming it. Orchard only through `B/tools/ossh.sh`; opaque names on Orchard (`a15_cot_ap` plus hex; no project, benchmark, dataset, model or method word). Streams above 20 MB register with the IO governor. Lane folder `/scratch/jjyeung/orch_n30/a2_dense`; events `B/events/a2_dense/`.

## Why
The A2 kit says GO=false. Its rows are lane rows_a2's work and its tree is lane tree_rebuild's (build 6): do not duplicate either. Nobody owns the material GF-1 needs beyond them: a dense 64-frame sample for every video row, the tower's cost, the cache that cuts it, and the leg's stop rule. Plan of record: `distill_design/DENSE_FRAMES_PLAN_20261115.md` (its lane's scripts and outputs were lost with trinity-2-18; recompute what you need).

## Inputs
- `DENSE_FRAMES_PLAN_20261115.md` (demand 3,048 clips; ScanNet and ScanNet++ nest from the k6 store, 993 of 994 in-map clips need no new decode; ARKitScenes needs 43,008 new frames from Apple's raw `lowres_wide.zip` by HTTP range reads, about 3 GB; pose rows' clip windows unknown), `GF1_FUSION_CONNECTOR_20261111.md`, `NEXT_LEG_TREE_REBUILD_20261115.md`, `NEXT_LEG_REBUILD_PLAN_20261115.md` (rows 25 to 34 and 119 to 122), `A0_AFTER_NATIVE_READ_DESIGN_20261116.md` section 5 (E2), `NEXT_LEG_INIT_RULE_20261116.md`.
- Tree and kits: trinity-1-3 `/scratch/jjyeung/orch_n30/tree_rebuild_w` (out/FRAME_HOST_JOB.md, PRELAUNCH_CARD.md, kits under work/build5/kits and build 6 when it lands); state in `B/events/tree_rebuild/STATUS.md`. Rows: `B/events/rows_a2/STATUS.md` (its item 4 qualifies the frame-host inputs that already exist; coordinate through events, never edit its files).
- k6 replica on Orchard `/project/community/jjyeung/cp4tk_fr/k6tk` (recorded 2026-11-13, unchecked); K1's ARKit fetch plan and frame parity results (`B/events/k1_ops3/STATUS.md`: byte pins broke on 40% of ARKit frames across decode library versions, so pin the decoder versions or pin decoded pixels with a tolerance).

## What to build
1. Dense manifest builder: for every clip of the four streams, a nested 64-frame sample keyed by content (the tree's one dense rule), from k6 extras; a metadata-only pre-pass that reports refusals before any RGB read; the 586 off-map `units` clips and the 759 mismatched camera-row references each admitted or deferred with a reason, the denominator kept.
2. ARKitScenes fetch packet for Orchard (a CPU job on general or inside the frame-host job): range reads of 1,409 captures, decoder versions pinned, parity against the student pins reported. First test: one ranged GET from an Orchard node (egress is unproven).
3. Pose rows: stream the pose row store where it lives and count, for the 18,547 retained rows, how many have a nested 64 inside their posed ordinals; state the new decodes.
4. Tower cache for the non-pose streams: a `cached_bank` input to the connector's pooled bank, a writer (about 51 MB per clip, about 156 GB for 3,048 clips; check the real merger grid first), and the parity test of the plan's section 6 item 5 on one real row in the trainer's dtype. Pose rows keep the online tower.
5. Measured cost: a packet for one H100 step with GF-1 on a real batch (online and cached), to replace the guesses of 345 and 190 GPU-hours per 1,000 steps.
6. Shuffled-bank read mode for the milestone reader: the same checkpoint read with each clip's geometry bank swapped for another clip's. It is the no-information baseline of the leg: a model that uses geometry must drop under it; no drop means the gain came from steps, not geometry.
7. The registration card (a draft for ORCH, registered before launch): question; the bundle (A0 rows, GF-1, D0 init per the init rule); stage 1 = 400 steps with only the connector training, stage 2 = 600 full steps; reads at stage-2 steps 100 and 200 against the init, paired by room; stop if F1 fails, or if the mean paired difference over object size, relative distance and counting (450 items) has its interval wholly below zero at stage-2 step 200, or if the shuffled-bank read equals the true read within 1 point on that mean at stage-2 step 200; alarms checked against a measured first batch (lesson of D0's first alarm); confounds: tower exposure (G3T may have seen benchmark scenes; disclosed), no held-out rooms for any descendant of step 544, D0's nine confounds, bundled rows.

## Tests
Manifest builder unit tests (nesting, content keys, two-clock scenes), the pre-pass on the full row metadata with zero unexplained refusals, cache parity on CPU with a tiny tower, the every-rank CPU first batch with fusion features on real frames inside the frame-host job (the tree's own gate), export and reload of a GF-1 checkpoint on CPU. No test writes a real-size checkpoint.

## Do not touch
D0 job 170111 and its Orchard roots, the VSTI read, K1, the sealed LEG-S1 kit, the tree and row lanes' folders (read only). Nothing goes to trinity-0-13 or trinity-1-13.

## Deliver
`out/A2_DENSE_READY.md` (counts, hashes, the three unknowns closed or stated), the packets, the draft card, mirror on a second node, STATUS.md, RESULT events. Review: one independent refute review of the manifest rule, the cache parity and the card's stop rule before the frame-host job.
