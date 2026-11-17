# Brief 03 (build): row store v7 for leg R1, recovery statuses, and a dev set for the VSTI relative types

Carrier: Codex gpt-6-astra, effort high, dispatched by a rows lane (Devin Opus, medium) on trinity-1-3 in a new folder `/scratch/jjyeung/orch_n30/rows_r1` (cap 6 GB; the store is 1.6 GB, check `df -h /scratch` first). Box: 3 hours. CPU only; no Git, no deletion, no Orchard call. First read `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`. Lane rows_a2 has exited; its folder `/scratch/jjyeung/orch_n30/rows_a2` is read-only input.

## Why
Leg R1 (design record `/data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_DECISION_20261117.md`) trains store v6 plus three things it lacks: direct room rows, away rows in ReVSI's own wording, and recovery rows for every status the reader prints. It also has no mid-leg read of the VSTI relative types.

## Inputs
- Store v6 and its build and check code: `/scratch/jjyeung/orch_n30/rows_a2/out/a2_vqa_v6/` (`vqa/rows.sqlite` sha256 0608dd98..., `CHECK_MERGE.json`, `VALIDATOR_FULL.json`), `/scratch/jjyeung/orch_n30/rows_a2/work/` (`build_a2.py`, `check_a2.py`), the VSTI generator under `/scratch/jjyeung/orch_n30/rows_a2/vsti/`.
- Room rows: `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/rows_slices/slices_final/a0_room.jsonl` (476) and `/scratch/jjyeung/orch_n30/rows_a2/out/a2_room_ft2_v1/` (95).
- Away renderings ra, rb, rc and the rows-lane rule: trinity-1-18 `/scratch/jjyeung/orch_n30/b13_facing/out/renderings/` and `out/RULE_rows_lane.md` (design record `FACING_AWAY_DIAGNOSIS_20261116.md`). Fetch them with one `tools/tssh.sh` call as a single tar under 20 MB.
- Recovery rows and their builder record: `slices_final/a0_recovery.jsonl` (1,532 rows, every one `not seen`, built by `work/a0/build.py` of lane rows_rebuild on trinity-1-13; the row's `provenance.details` names the formatter lines).
- The status census of lane notseen_diag: `/data2/jjyeung/agent_project_data/distill_design/H1_0_NOT_SEEN_DIAGNOSIS_20261117.md` when it exists (due 16:41Z); until then use the strings the tree formatter prints (`trace_format/box_v313.py`, `ground_v313.py` in `/scratch/jjyeung/orch_n30/tree_rebuild_w/work/tree_r1`).
- Validator a41ba191 and the exclusion lists as rows_a2 used them (`/scratch/jjyeung/orch_n30/rows_a2/work/`): BENCH v2 3119aa4a, dev-S1, WITHHELD_ROOMS_80 634820b4, K1 held-out, R0 rooms bdb5d402.

## Work
1. **Store v7** = v6 + the 476 direct room rows + the 95 square-feet rows + away rows in the wording "facing in the opposite direction of", rendered as `RULE_rows_lane.md` prescribes, so that this wording carries about one third of the away twins. Keep v6's rows byte-identical. Report rows per type and per dataset (ScanNet, ScanNet++, ARKitScenes).
2. **Recovery statuses.** Add simulated `box unavailable` rows (about one fifth of the recovery family) in the same trace form, and any other status the census shows the reader printing after a ground call. Each status string must be byte-equal to the formatter's output. Report counts per status and per missed operand.
3. **Dev set for the VSTI relative types.** With the generator that built the 11,926 training rows, write 150 items for each of the six types on R0-dev rooms only (frames and ground truth: lane b10's archive `/data3/jjyeung/n30_b10_reserve/`, read through the IO governor if above 20 MB). These items are never trained. Add to each item a flag the scorer can use for template capture: whether the trace treats the camera as an object "first seen in frame N".
4. **Checks.** Validator a41ba191 with 0 failures on every new row; an independent recompute of every new answer; 0 exclusion hits for training rows; 0 duplicate qids against v6.

## Gates
`CHECK_MERGE.json` and `VALIDATOR_FULL.json` PASS for v7; v6 rows unchanged (hash of the v6 subset equals v6); the dev set shares no room with any training stream.

## Outputs
`/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/` (store, receipt, manifest, checks), `out/recovery_v2/`, `out/vsti_rel_dev_r0/`, `out/ADMISSION_PACKET_V7.md`, a mirror on a second node, and one RESULT event that asks for one refute review.
