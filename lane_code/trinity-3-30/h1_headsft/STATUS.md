# h1_headsft STATUS (Devin lane on trinity-3-30; started 2026-11-16T12:51Z; session ends ~18:45Z; rotate RESULT before then)
Brief: design + build H1 (head-routing SFT on GT head-calling traces). L=/scratch/jjyeung/orch_n30/h1_headsft. Events: orch_n30/events/h1_headsft/.
## Rulings in force
- ORCH GO 1342Z: H1-0 (step 544 then D0 m200) after cross-family review + CPU first batch, on trinity-1-13 cards that gpu_fill2 names (vnice), export + SAM 3 read in place from /dev/shm/jjyeung (cap 60 GB, ~54 used: stage only what is missing, <=6 GB, else 1-18 cards) or Orchard general after D0's m200 stop-rule read; <=3 cards; reuse b04 E2EGenerator (no fork). H1-1: GO in principle for Orchard advanced at the end of D0's FIRST allocation (USR1 ~06:25Z 11-17), before D0's second allocation and A2, iff reviewed + every rank's CPU first batch + H1-0 on step 544 landed; else D0 continues. Make the faithful fix a separate tested patch and tell tree_rebuild4 (build 7). H1-2 priced in the record (done). M1-M3 bars + control registered in the record (done).
- ORCH 1257Z: evaluator standalone with fixed item sets (RL reuse by b09). ORCH 1307Z: R0 rooms (R0_ROOMS.txt bdb5d402, copy L/work/auth) out of every stream; report count removed (b10 check: 0 in D0 VQA/kit07 frame map/A3/dev-S1/ReVSI).
## Done
- Design record distill_design/H1_GT_HEAD_ROUTING_SFT_20261116.md (latest sha256 58148fa2...; lane copy L/out/) + INDEX line. RESULT 1335Z design_go_request.
- Build 1 (Codex h1_kit1, 13:29-13:53Z) in L/kit: trainer patch (S1 faithful own camera rows via derivgen materialize, S2 pose targets, stop_after_step), rows tools, configs h1_1/h1_1a (+diff_against_d0), evaluator h1eval over b04 E2EGenerator, tiny world-4 first step. My rerun in copy L/work/verify1 (logs L/work/verify1/vlogs): unit 11 OK; faithful 12/12; OFF identity 4 ranks x 72 microsteps exact; eval 4 pass 1 fail (scale_scene gap criterion; fixed in build 2 by comparing to the printed perturbed value).
- Note to b04 inbox 1359Z: H1-0 rides on b04's parity-read factory on 1-13 (perception_factory hook); default: H1 wraps it, no b04 file changes.
- Review brief written: L/briefs/review_h1kit.md (Devin Opus reviewer writes REVIEW_VERDICT_H1KIT.md into events/h1_headsft/).
## Facts for H1-0 (checked 14:05Z)
- trinity-1-13: 1 TB RAM (593 GB avail), 96 cores, /scratch 64 GB free (floor!), /dev/shm/jjyeung/exports/m544 = HF-format LM shards only (no heads.pt); cards 0,6,7 idle at 14:04Z; envs planner_local_v1, vllm only.
- Own heads file heads.pt (sha256 8bb5e151..., in artifact m544/artifact.json) is inside trinity-1-18:/scratch/jjyeung/k1/m544_parts/469ddece_mstop.tar.part0{0..3} (4 x 5.4 GB). b04's parity read needs it too (own gravity head): share one stage.
- dev-S1 items: direct 1,525 = b01_d0guard/guard_kit/report/inputs/TASKS.jsonl (a2f3fdbd); distance list DISTANCE_LIST_DEVS1_150.jsonl; camera 450 = R1.json keys devs1cam-* (b04 work/n13/ret/native/R1.json, no question text; generator c8r .../native/out2/camera_cohort.py); ReVSI 999 = b07_offread/in/kit_revsi/inputs/i1.json (283 abs distance, all metres; 37 room).
## In flight
- Codex build 2 h1_kit2 (started 13:55Z, tmux h1_kit2): prompt L/prompts/build2.md (CLI items/run/pair/curve with pinned sets, R0 exclusion, M3 criterion fix, separate faithful_own_rows.patch + FAITHFUL_FIX_FOR_TREE.md). Receipts agent/scratch/codex_runs/20261116T135508Z_h1_kit2.
## Next
1. Build 2 ends: rerun tests in a fresh copy; send faithful patch + note to tree_rebuild4 (trinity-1-3 /scratch/jjyeung/orch_n30/tree_rebuild_w/inbox) and an event line.
2. Launch reviewer: `bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/devin_bg.sh review_h1kit /scratch/jjyeung/orch_n30/h1_headsft/briefs/review_h1kit.md claude-opus-5-5-high 7200` on 3-30; RESULT kit_ready_review_started.
3. Mirror L/kit (tar, ~0.45 GB) over IB to trinity-1-18:/scratch/jjyeung/n30_mirror/h1_headsft/, sha256 both.
4. H1-0 launcher on 1-13: wraps b04's parity factory (when it exists) + h1eval own perception; CPU first batch on 1-13 (real export, one item per call type, own arm + one perturbation); stage heads.pt (<=6 GB) shared with b04.
## Defaults in force
- No GPU, no Orchard submission until review GO + ORCH card. ReVSI first. Frames 32 (64 refused by trainer). SFT first; RL kits built ahead only.
