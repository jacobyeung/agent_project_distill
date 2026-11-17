# Brief 05 (operator): tower-arm read of step 544 on the dev-S1 routed items

Carrier: Devin Opus, medium effort, on trinity-1-3, lane `tower_read` in `/scratch/jjyeung/orch_n30/tower_read` (cap 2 GB); Codex gpt-6-astra high only if the package refuses the tower arm. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. One H100 on Orchard general, submitted only after the orchestrator's GO and in the order of the design record's section 4 (after R1's production proof); main has priority; one distillation job at a time. Official benchmark items are not read.

## Question
On one reader build and the same 636 dev-S1 routed items, how do camera, distance and room reads of step 544 differ between the own arm (H1-0, already read: Orchard 170631, 170694, 170706) and the tower arm: G3T pose and depth inside the call, scale = median(own depth / G3T depth), own gravity, SAM 3 on the raw name with the selector head, `bestspread` lifting on tower depth? The answer fixes the head-serving table of `/data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_DECISION_20261117.md` (section 1) by measurement.

## Inputs
- H1-0's package on Orchard: `okh7/e6fc152498/` (package b01ec87a6f29b, `0.tgz` 446a4323; b04's reader with the types option and the per-read call cap), its scorers, and its returns under `r2/sj/` (H1 record `H1_GT_HEAD_ROUTING_SFT_20261116.md`, Status). Lane files: trinity-1-3 `/scratch/jjyeung/orch_n30/h10_score/work/` (results, scripts copied from trinity-1-18).
- b04's reader and its tower-arm wiring (`real_perception`, `OwnDepthScale`, `lift_bestspread`): copy on trinity-1-3 `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/design/b04_v8/` (961295be, read-only), mirror trinity-1-18 `/scratch/jjyeung/n30_mirror/b04_e2ehook/`; record `E2E_READER_B04_20261116.md`.
- G3T weights and the step-544 export as job 170056 staged them (events of lanes native_r2 to native_r5).
- The H1 evaluator after its re-pin (ORCH 1356Z in `events/cont_ops/`): export pins are a parameter; use it with the step-544 pins.

## Steps
1. Add the tower arm as a perception option of the same package (pose source, depth source and scale source named in its config; nothing else changes). If the package already carries it, only write the config.
2. CPU check with the production config in the job's real node environment from an empty root: the step-544 binding reproduces 46029ca2, and one item per type runs through the tower arm on CPU.
3. Read plan: baseline decode of all 636 items on the tower arm (camera 450, distance 150, room 36; the call caps of the H1 registration apply). No perturbed decode.
4. Score with the package's scorers and pair by item with H1-0's own arm: per type task accuracy, own minus tower with a room bootstrap (10,000 draws, seed 20261115); per-call errors; for distance the share of reads with a `not seen` response, with each other status, capped reads, and MRA on metre questions and on reads without a failed ground.

## Gates
Identity proof on the binding; every item has a finish reason; the paired table covers all 636 keys or names the missing ones.

## Outputs
`out/TOWER_ARM_DEVS1.md` and `curve.json` in the lane folder, the returns' sha256, one RESULT event with: own minus tower per camera type with intervals, the `not seen` rate on each arm, and whether any type meets the take-over bar (lower bound above -5). Append the numbers to the design record's section 1.2.
