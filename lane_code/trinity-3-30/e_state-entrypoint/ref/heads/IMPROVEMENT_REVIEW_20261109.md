# Improvement review of the live plan (2026-11-09 07:30Z)

## Question
User (23:25 PT): progress? eta? can we improve? Judge three critics' proposals (schedule, portfolio, read validity) against the handoff, lane STATUS tails, evalx events and the grounding design; keep only verified actions, ranked by value per hour of delay.

## Answer: top 8 actions
1. evalx (dispatch a Codex implement worker now): land the point-only size fix in tp/programs.py vis() (lines 385-389 give point clicks size 0, so best_frame/choose_frames pick the earliest clicked anchor), then run Test 0/1 (H+OP fused, -spec-fix, agg with abstain-to-direct, O1/O2) on the t0m600 clicks; cp1_table.py ROWS gain the fixed rows and refuse to publish without them. Impact: 0 GPU-h; decides which VSI types route in CP1 (P1 loses 20-37). Deadline 09:30Z, before the in-video table.
2. ORCH + ghead + pose_sweep: give GH0 the 8 GPUs that would go to CPARAM at the ~07:40Z handover, once its 1-GPU first batch passes; chain the 4-GPU P1-GH eval afterok. Impact: grounding read ~13:00Z instead of ~23:00Z (which falls after AWS stops); net 0 GPU-h. Deadline 08:00Z.
3. ORCH + t1_build: pre-register at 08:40Z that T1 continues only if m400 beats T0 m400 on direction or centre (CI excludes 1) or VQA slice >= T0+3; else cancel 119551/119781 before ~08:50Z, keep its last checkpoint, drop the CP1-from-T1 kit (121370), and give the 32 to GH0, evalx (+4), GX/pose and pt-track. T2's matched read stays at m400/~m550. Impact: ~128 GPU-h in the 09-13Z window. Deadline 08:40Z.
4. gx_build, ghead, p3_build: set each kit's leg budget p95 from measured pace +30% (RES2 stopped at step 170 on a 60 s p95 vs ~16 s real); put the decisive milestone inside leg 1; measure GX-ft's first 20 steps. Impact: ~15-30 GPU-h and 20-30 min per read. Deadline 07:40Z GX launch.
5. evalx (CPU): rerun run_conditions on the dev pool with GT clicks and own depth under own, G3T-probe and GT pose; if GT minus own pose < ~3 points on VSI types, drop PAIRS/DR/MC8 and run only arms that stack on the GX winner. Impact: ~40-60 GPU-h saved. Deadline 10:00Z (before the GX m200 read).
6. p3_build: the final-config CP1 GPU first-batch check (all 32 ranks) must pass before 15:30Z, since no AWS GPUs run 16-20Z and the cpu partition is stuck; decide by 12:00Z whether CP1 trains both direct and routed rows for the P4>direct types behind a mode token, so a later GH0/agg win needs no new 32-GPU run. Deadline 12:00Z / 15:30Z.
7. ORCH assigns one lane (posedata2): run the stuck CPU jobs (posedata2 120140/120141/120204, streams2 120053/121258, t1 121370 if kept) concurrently in one 1-GPU + 64-96-CPU GPU-partition job; ask the user once whether the cpu nodes are drained (default: keep using GPU nodes). Impact: CP2 rows 3-6 h earlier, pt-track rows 1-3 h earlier. Deadline 08:00Z.
8. ORCH + streams2 + orchard_kit: pt-track cannot finish on AWS as planned (read ~19:00Z, AWS stops 16:00Z, 20:00Z GPUs are CP1's). If 121258 rows land by 10:30Z, a separate Codex worker builds the Test 3 kit and launches 8 GPUs x <=3.5 h by 12:00Z; else orchard_kit builds a world-4 kit for the ~22:45Z Orchard slot. Keep p3_build on CP1. Deadline 10:30Z.

## Reasons and evidence
- Size defect confirmed in /scratch/jjyeung/orch_cd/evalx/work/tp/programs.py (mtime 11-08 13:13Z); cp1_table.py line 55 lists only H+OP-spec/H+OPm-spec; evalx STATUS through 07:18Z has no agg/size-fix/O1 entry although ORCH inbox 0606Z asked for it.
- Post-09:00Z cap 112 = T0 32 + T1 32 + T2 32 + GX 12 + evalx 4: no slot for GH0 or pose arms until ~13:00Z (handoff 06:07Z, 06:55Z).
- T1 m200 = T0 m200 on pose (07:07Z); CP1-from-T0 config b72d09e3 already uses T1's pointing f/7883606f (p3_build 06:51Z).
- P4 (GT clicks, own pose ~20 deg) beats direct by 18-31; own clicks lose by 20-37 (evalx 0600Z).

## Rejected
- Start the real CP1 run at 14:15Z (critic 1): T0 final (~13:30Z), the GH0 read (~13:00Z) and an 18:30Z data change would force a restart from step 0; only the first-batch check moves earlier (action 6).
- The T0 VQA drop 52->45 is an off-interface artifact (critic 3): every milestone and base use the same no-marker vLLM layout, so the m400->m600 drop is a within-interface change; markers matter for VSTI frame types, not this slice.
- Routing decided on the test set (critic 3): ORCH ruled dev-only at 04:54Z; the full-5,130 preset is pre-registered for T2-vs-T1 only. Already done.

## Risks
- CP1 freezes at 18:30Z with a route table built on buggy or harness-only clicks, then fills the only 32 AWS GPUs to 11-19 with a direct-only model; actions 1, 2 and 6 address this. Watch: the in-video table and the GH0 read land before 15:00Z.
- GX gain may be ScanNet memorization by G3T (GX design record): read the ARKit bank before CP2 adoption.
- Stopping T1 loses T2's matched control past ~m590.
