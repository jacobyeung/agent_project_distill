# Distillation handoff, 2026-10-28 04:30 PT (11:30Z)

Orchestrator agent-project-distill-52, Claude session 48e156e2 on trinity-0-13. L = `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/lanes`.

## 1. Goal (USER /goal, 10-27)
A 9B or 27B VLM trained on traces scores at least 70 on VSI-500, beats its matched direct-answer control on 2 seeds, and holds or improves on VSTI and one other spatial benchmark. Every night the AWS share is full, every run is scored by morning, and the Gemini key and the open-model cascade never sit idle. The user also says: use any model that helps, set no arbitrary limits, and run 27B when it gives more signal.

## 2. Standing rules learned 10-27/28 (also in memory)
- **AWS share:** distillation holds DISTILL_NIGHT_SHARE (`L/aws_reserve`) from 18:30 to 06:20 PT, normally 168 and up to 268 when the priority project is light, and 16 by day. The account's running GPUs stay at least 80 below the 10th-largest user's (`squeue -t R`, %b times %D). The cot_faithfulness project's requests win. Cancel newest jobs first.
- **No compute on the code-aws login node.** Use Slurm (`-p cpu` for CPU work).
- **The Lustre file quota (about 26.21M files per user) is the binding AWS limit.** It filled at about 02:30 on 10-28. The trainer writes one file per row, and sharded targets (trainer 9183d0d) fix that. Count a job's files before submitting it.
- **No lanemsg, ever.** Its SSH fan-out broke the admins' 12-session cap. Agents open no sessions to non-allowed nodes (allowed: 0-13, 2-18, 2-23, 3-3, 3-30) or to the head node.
- **Copy queue** (`/data3/jjyeung/orch_n13_20261026/copy_queue`, HOWTO.md): admission_order takes exact IDs only, via orchestrator-n13. Withdraw a job with withdraw/<id>.json. Pass-through pulls go AWS → trinity-3-30.
- **Claude transcripts live on /data2,** so many spawns or resumes cause IO spikes. Keep both rare.

## 3. Results so far
- **Matched readouts on AWS:** trace arms trail the direct control (MIX ties on VSI, +0.07; 2222 −3.7; SELF_V4 −5.6). See `L/awstrain_20261027/results/READOUT_20261027.md`.
- **Heads:** null at 12k rows. Frozen-feature probes show distance, position and camera translation are not decodable at any layer (`L/probe_decode_20261027/RESULT.md`).
- **A1 at step 500** (rung-1, 290k GT rows): reads first-seen time at 63% against 23%, but not counts. On the harness it scores −8.3 VSI and −10.9 VSTI against SELF_V4_C_S17 (unmatched), with forgetting on types that have no rows (room size −35, route −14, VSTI types). A1H's heads hurt its language model.
- **Rung-1 job deaths:** A1, A2 and A1H were cancelled by a same-account cancel after outside srun samples (probably cot_faithfulness's idle check; the user has been asked). The stalls came from Python garbage collection, fixed by closure f344aa6b (gc.freeze).

## 4. Data supply
- **Gemini:** 203k kept at 04:23 PT, about 40k per hour (`L/vsi590k_gemini_20261027`, GEMINI_HEARTBEAT). The qgen waves are certified at 36/40.
- **Checker KEEP:** 31,582 rows (34/40). **ADT:** 60,103 rows, audits 39/40 and 40/40. VSI-590K's released ADT direction labels are wrong.
- **Hypersim fix1:** 97,745 rows, single image, so not in rung-2. **Cascade:** 5,238 trusted rows; it goes Qwen-only from now on.

## 5. Tomorrow night (10-28, `L/rung1_build_20261027/night_20261028/PLAN.json`; the loop plans at 18:20)
A1 s17 resume + A1 s18, the 27B A1 and 27B X_full pair (64 GPUs each), then 9B X_full s17/s18 at world 64. New arms checkpoint every 200 steps on closure f344aa6b. Rung-2 (393k rows plus a matched control, sharded targets, type-coverage fixes) and the geo pilots G/G-XA are being readied for 10-29.

## 6. Live lanes (Claude subagents of this session)
rung1_build (launch and babysit), rung2_build (plus vsti/room sub-lanes), vsi590k_gemini, vsi590k_cascade (idle until tonight), geo_input, inode_inventory. Finished: perchead (A1P waits on camera-calibration copies), checker, ADT, evalfix (eval_sched PID 411289, 27B-aware), probe_decode.

## 7. Open with the user (SAVED_USER_QUESTIONS.md)
- A safe-first delete command (about 310k AWS files), sent by orchestrator-n13.
- Stopping the same-account cancels of a15_cot_ap* jobs.
- Re-allowing the packing lane under the split/distill waiver (the classifier blocked it).
- ScanNet HF tarballs (49 GB, needs an admin window) and ytb_roomtour (55 GB).
