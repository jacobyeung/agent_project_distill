# Distillation: current state (single writer: the orchestrator; rewritten at each ruling, never appended)

State as of 2026-11-16T11:23Z (snapshot `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/ORCH_STATE_SNAPSHOT_20261116T1123Z.md`). Read this page first; open the newest snapshot only where it is newer than this page.
B = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30`. Records cited by bare name live in `distill_design/` and are indexed in `INDEX.md` there.

## Goal
One trained 9B spatial student that answers by chain of thought using its own heads (SFT now; RL later rewards correct and short chains), beats GeoWeaver-10B (75.05 VSI) and the frontier closed models, then makes VLA fine-tuning cheaper and better.
Second goal and its kits: group "VLA and dynamic scenes" of the index. Memory note goal-cot-heads-foundation-for-rl-20261116 holds the user's words.

## Live runs
| Run | Where | Owner lane (events) | Ruled by |
|---|---|---|---|
| D0 training leg: sealed LEG-S1 trainer, row store v5 4af43b40, warm start from step 544, 1,000 steps | Orchard 170111 (a15_cot_apddbe32d7), advanced, 4 H100; exports m100 ~13:55Z, m200 ~17:50Z, m400 ~01:40Z 11-17; USR1 ~06:25Z 11-17 | cont_ops6 (B/events/cont_ops/STATUS.md) | `D0_STOP_RULE_20261116.md` sha256 7a487e63; a STOP or CONTINUE verdict comes to the orchestrator before anyone acts |
| VSTI-450 native read, camera calls only, kit V1c dc40cf60 | Orchard 170209, general; one resubmit with b.tar 0eadd83e (ORCH GO 1121Z); off general before the D0 step-200 read | native_r5 (B/events/native_r4/STATUS.md) | `VSTI_NATIVE_CAMERA_READ_STEP544_20261116.md` |
| K1 own phase (step-544 depth and gravity heads on 300 captures) | Orchard general after VSTI; 170206 ended, root cause stage_job.py dropped step_400 depth files | k1_ops6 (B/events/k1_ops3/) | `REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md` sha256 ab687d7d; `REFREEZE_AMENDMENT_2_K1_MANIFEST_V2_20261116.md` sha256 25df15e0 |
| Next-leg rows (A2) | trinity-1-3, headless Claude lane | rows_a2 (B/events/rows_a2/) | `NEXT_LEG_INIT_RULE_20261116.md` sha256 a733a26a |
| Next-leg tree build 6 | trinity-1-3 | tree_rebuild3 (B/events/tree_rebuild/) | `NEXT_LEG_TREE_REBUILD_20261115.md` |
| Trinity read path (20-item proof, then step-544 baseline) | trinity-1-3 / 1-18 card when empty | trin_read3 (B/events/trin_read/) | `TRINITY_READ_RUNTIME_20261116.md` |
Orchard general takes one job of ours at a time, in this order: D0 m200 read, VSTI, K1, D0 m100 read (B/events/, ORCH_RULING_general_order).
Check a job: `bash B/tools/ossh.sh 'TZ=UTC squeue -u $USER -h -o "%i %j %P %T %M %l %R"'`; our names start a15_cot_ap; jjy_* jobs belong to main.

## Nodes
- Orchestrator: trinity-3-30 (tmux distill_orch). Lanes: trinity-3-30, 1-3, 1-18.
- Down, never wait for them or ssh to them: trinity-2-18 (orch_cd) and trinity-2-28 (orch_n28). What survives: `RECOVERY_MAP_2_18_OUTAGE_20261115.md`.
- Never: trinity-0-8, 0-23, 3-23; nothing on 0-18 (main's). Stage nothing on 0-13 (/scratch at main's 150 GB floor) or 1-13 (71 GB free).
- Every large-GPU node except 0-13 runs under vnice. Two fresh nvidia-smi readings 5+ minutes apart before a launch.

## Standing rulings
- Cluster rules: section "Key Trinity Cluster Rules" of the global CLAUDE.md wins over everything here; lane rules `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/LANE_RULES.md`.
- IO: every stream above 20 MB on /home, /data* or across the head node goes through the IO governor; README `/data3/jjyeung/orch_n13_20261026/io_governor/README.md`.
- Trace grammar: programs only for absolute distance, room size and the three camera types; direct rows qualitative, never empty, never with stated measurements: `TRACE_RULING_20261115.md` (room row of 2.2 under review).
- Grounding in the repair seal: no new trainable module; the deployed frozen backend grounds; K1 is the kill test: `B6_GROUNDING_DESIGN_20261115.md`.
- Benchmark scenes stay out of every training stream: `BENCH_SCENE_EXCLUSIONS_20261108.md`; check any init's training scenes before a comparison: `TRAIN_EVAL_SCENE_AUDIT_20261110.md`.
- Routed-path re-freeze before any native official read of VSI-Bench or ReVSI: `REFREEZE_PREREGISTRATION_20261115.md` sha256 ca4a4fbe; `REFREEZE_PREREGISTRATION_20261115.json` sha256 6375d400; `REFREEZE_AMENDMENT_3_D1_D2_ROUTE_DECISIONS_20261116.md` sha256 95638788.
- Init of the next leg (A2 or A0) follows `NEXT_LEG_INIT_RULE_20261116.md` sha256 a733a26a, registered before any D0 export was read.
- D0 stops by `D0_STOP_RULE_20261116.md` sha256 7a487e63 (amended 09:45Z, before any export).
- No LEG-S1 continuation without the user's yes: `LEGS1_CONTINUATION_PRELAUNCH_20261115.md`.
- Executors: Codex is the default builder (agent/scripts/codex_dispatch.sh, Astra for hard builds); Devin lanes outlive Claude sessions; Claude subagents and Fable freely until 23:00Z 11-16.
- Commit lane code often: hourly lane_code_sync (tmux lane_sync on 3-30), one Git owner, never rewrite history: `CODE_SYNC_20261116.md`.
- No deletion command by any agent; removal candidates go to REMOVAL_CANDIDATES.md files for the user.
- Mirror every sealed kit, accepted packet or finished dataset to a second node at once.
- Before telling the user what a comparison means: who trained on the evaluation scenes, and which units each number covers.

## Results that bind
- Official VSI-Bench direct, step 544: six direct tasks 68.77 [66.5, 71.0] vs f17 65.60; abs distance and room not read; never compare to 63.79 or 75.05: `OFFICIAL_VSI_DIRECT_STEP544_20261115.md`.
- ReVSI direct, step 544: five categories 64.94 [61.3, 68.4]; away 14.0 vs toward 88.3; never compare to 58.63 or 57.5: `REVSI_DIRECT_STEP544_20261115.md`.
- Native routed read, dev-S1, step 544: programs emitted 99-100%; camera 82.3 / 94.7 / 75.7; the student answers in metres whatever unit is asked; distance vs parent -9.0 [-17.0, +0.2], all on non-metre questions: `NATIVE_ROUTED_READ_DEVS1_STEP544_20261115.md`.
- Official VSI-Bench routed 64.76 vs 63.79 is NOT clean: off the selection scenes +0.42 [-0.23, +1.08]; seven routed-path choices were made on benchmark items: `POLICY_AUDIT_20261115.md`.
- Route table after the native read: programs for absolute distance and camera types, room direct, recovery and unit rows: `A0_AFTER_NATIVE_READ_DESIGN_20261116.md`.
- E3: no scale or floor rule makes room routable (63.3 vs f17 direct 63.4) or adds more than about 3 points on distance: `E3_BACKEND_GEOMETRY_PRICING_20261116.md`.
- Gap to GeoWeaver: about 7.9 VSI points (estimate 67.1); counting, appearance order and object size hold 6.4: `NEXT_QUEUE_20261116.md`.
- Frontier closed models, no tools, 32 frames: Argon 76.68 VSI-500, Carbon 75.97: `FRONTIER_READ_20261111.md`.
- IF-P0 (vision-only branches in LM layers 1-8) closed NO-GO: `IF_P0_FINAL_20261115.md`.
- Pose limit is the Qwen encoder; pose comes from G3T: `POSE_PLATEAU_DIAGNOSIS_20261109.md`.
- K1 tower phase complete 300/300; GT rasters rebuilt to their pins; refit inputs recovered: `K1_REFIT_INPUT_RECOVERY_20261116.md`.

## Do not redo
- Direct reads of the parent or f17 on the 450 camera keys (a 41 to 72 point gap changes no decision).
- Any scale or floor rule run (E3). A V1e of the VSTI kit; the staged code tar is dc40cf60. A second pull of the base tar (lane trin_read3 holds it).
- An official native read of VSI-Bench or ReVSI before the re-freeze; on VSTI only camera calls are served.
- The direct reads of LEG-S1 steps 100, 200, 400 and 544 (accepted packets); IF-P0's P0 and IF8 arms; any retired native family or token.
- The diagnoses of the parity probe, the first routed items, the geometry guard and the native pin graph (index group Archive, topic "Routed read ...").
- The state copy to GCS for 169097 (closed); the MDG line (MDG-A NO-GO and ineligible as an init); T2 and C1 sweeps.
- The teacher r5 pass, the P7 audit, the Argon/Carbon/Astra labeler comparison, the 3D-box pilot, the VSTI e2e and direct reads.

## Ready-to-launch queue
Ranked by `NEXT_QUEUE_20261116.md` section 2; GPUs named are the only ones we hold.
1. D0 milestone reads (m100 no verdict, m200 verdict, then 400, 600, 800, final) on Orchard general with the confirmed D0 read kit; cont_ops submits.
2. VSTI-450 camera read (170209), then K1 own phase on Orchard general.
3. A2 leg (A0 rows plus geometry fusion) on the four H100 when D0 ends or stops: needs rows (rows_a2), tree build 6 plus its second review, and the init rule's guard reads.
4. Init-rule guard reads, about 1.3 H100-hours per candidate: kits are queue briefs 01 and 02 (not built).
5. Second D0 allocation (resume from the end slot) at ~06:25Z 11-17 unless a verdict says STOP: not yet ordered.
6. Trinity read path: step-544 baseline and D0 milestones on a 48 GB card once the 20-item proof passes.

## Open user decisions (asked once; never repeat unprompted)
- LEG-S1 continuation yes or no (packet ready, unsubmitted).
- D0's 19,146 procedure-only rows (kept by default).
- Whether the admins know trinity-2-18 and 2-28 are down; the removal lists.

## Where to look next
- Index of design records, grouped: `INDEX.md` in distill_design (groups: Results that bind; Active and next leg; Rulings; Grounding; Pose and geometry; Traces and pools; Orchard, infrastructure and tools; VLA and dynamic scenes; Archive).
- Student architecture: `ARCHITECTURE_CURRENT.md`. Rebuild of lost work: `NEXT_LEG_REBUILD_PLAN_20261115.md`.
- Lane state: B/events/<lane>/STATUS.md; briefs B/briefs/; tools B/tools/ (launch_remote.sh, devin_bg.sh, claude_bg.sh, evwait.sh, ossh.sh, tssh.sh).
- Ruling log of a past night: search the snapshots under `distillation_orchestrator_20260918/`; never read one whole.
