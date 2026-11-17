# tree_rebuild STATUS (successor resumes from this file alone)
Updated: 2026-11-17T10:25Z by tree_rebuild4 Devin session 5 (trinity-1-3, started 09:07Z; must rotate by 14:50Z). Build 8 (Codex PID 2173030, since 05:02Z) final pass: seal and make_delivery done; FINAL_PASS.json shows legacy_guard_proof and packet steps failed (rc 1), Codex is recovering the packet (work/build8/packet_recovery.py, PACKET_RECOVERY.json); package suite tree legacy 1275/~1822 at 10:24Z (~15/min), then base groups, compare, coverage, EAT-1, report. Progress: `bash W/poll3.sh` (prints work/build8/monitor_status.py). Build 9 owed after it (W/prompts/build9_draft.md). Lane W 3.1 GB of 8.
Goal: next-leg source tree (A0, A2 kits) integrated, suites green, D1-D4 closed, EAT-1 run on CPU, then one second review. Percent done ~85%: builds 1-7 done; build 8 running.
Lane W = trinity-1-3:/scratch/jjyeung/orch_n30/tree_rebuild_w (cap 8 GB; 1.9 GB). O = trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild holds builds 1-4 history (3.95 of 5 GB; do not grow).
Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/ (read every *_ORCH_* file there and W/inbox at each step). Poll helper: `bash W/poll3.sh [max_wait_s]` (set for build 8; returns early when meta.json appears). ORCH 1228Z: no checkpoint events; events only for questions, blockers, final results and rotate.

## Running now
- Build 8 (Codex gpt-6-astra high) in tmux `tree_rebuild_b8` on trinity-1-3, codex_dispatch PID 2173030, started 05:02Z. Prompt W/prompts/build8.md (items 1-9: 4 regressions without weakening tests, R2 to 0, 78 CPU gaps, multi-rank USR1 proof script W/work/build8/proofs/stop_multirank/RUN.sh, frame-count sites, portrait resize classification, legacy empty-think refusal, out-of-scope list, final pass). Receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261117T050224Z_tree_rebuild8. Status W/work/build8/STATUS.md; report W/out/BUILD8_REPORT.md. Poll every 10 min; tail only. Never start a second build while it runs.
- If build 8's Codex dies on an API error (meta.json exit!=0, no final_message.md): read W/work/build8/STATUS.md and dispatch a resume build (label tree_rebuild8b) told to resume from it. Do not rerun anything killed by the cluster.

## When build 8 ends
1. Read final_message.md and W/out/BUILD8_REPORT.md. Recompute the seal: `cd W/work/tree_r1 && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"`; it must equal W/out/TREE_SEAL.json `tree_sha256` and the package name.
2. Stop proof: at 05:46Z I ran build 8's then-current RUN.sh outside the sandbox (copy of Codex's own RESULT saved as W/work/build8/proofs/stop_multirank/RESULT.codex_sandbox.json; my run's log lane_run.log there): FAIL "USR1 did not reach both ranks" because of a driver bug (`shell.replace('X="$1"',...)` also rewrote HX, so the trap looked for h.py under the case root; not a tree defect). A fixed copy in W/work/lane_stop then hit Codex's newer driver import (stop_monitor), since Codex rewrote stop_multirank.py at 05:46Z. Leave work/build8 to Codex. After build 8 ends, if its RESULT.json is not a PASS from outside the sandbox, run `bash W/work/build8/proofs/stop_multirank/RUN.sh` yourself (outside the Codex sandbox Gloo works: 2-rank all_reduce on 127.0.0.1 passed 05:00Z, script W/work/tmp/gloo_check/g.py). CPU only, CUDA_VISIBLE_DEVICES="".
3. Mirror the package: `cat pkg | bash /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/tools/tssh.sh trinity-1-18.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild/<pkg> && sha256sum /scratch/jjyeung/n30_mirror/tree_rebuild/<pkg>'`; compare sha256; record both paths here.
4. RESULT build8 (suite counts vs base, regressions, R2, coverage classes, EAT-1, stop proof, blockers). Ask ONCE for the second review only if the full suite completed, regressions and R2 failures are 0 (BF16 parity may stay a named blocker with the option refused), zero CPU-reachable gaps remain, and EAT-1 ran on build 8; D2-D4 may stay named input blockers (other lanes own the inputs). Otherwise dispatch at most one more fix build.
5. Update the design record /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_TREE_REBUILD_20261115.md header (Answer/Evidence/Status lines) + its INDEX.md line to build 8.
6. Build 9 is owed regardless (ORCH 0647Z recovery rows; RESULT 0649Z recovery_rows_refused_by_gate): fill SEAL8, PKG8 and LEFTOVERS8 in W/prompts/build9_draft.md from BUILD8_REPORT (regressions, R2, CPU gaps, stop proof if still failing), save as W/prompts/build9.md, dispatch label tree_rebuild9 in tmux tree_rebuild_b9. Ask for the second review only after build 9 meets the step-4 conditions.
7. The frame-host CPU job on Orchard needs the orchestrator's GO with its packet; never submit without it.

## Build 7 outcome (ended 04:56Z, Codex exit 0; BUILD7_REPORT.md)
- Seal 26a635fc34aa97ac2909985ca4c1e1007c03e621ab95742d2a7c93a7b282b052 (878 files), recomputed 04:57Z = TREE_SEAL.json. Package W/out/tree_rebuild_b7_26a635fc.tar (107,018,240 B, sha256 3580d2f4034d4282f76280dd87526d3975d821eff89ae3e86ecfe4235d4ed0e0), mirrored trinity-1-18:/scratch/jjyeung/n30_mirror/tree_rebuild/ (sha equal 05:00Z). Kits A2 87d52101…, A0 8259dbab…, GO=false.
- Packet 202/202; tree 2216/1672, base 1842/1302; 474 pre-existing; 4 regressions; R2 2 failures; coverage 5716 observed / 78 frame-host / 78 CPU gaps / 3 GPU / 2 model-loader. Build 6's 4 regressions and 221 gaps resolved.
- EAT-1 tiny GF-1 and C8r: A1 PASS, A2-A4 FAIL, A5 INCOMPLETE. Items: D1 closed locally; D2 init_selection_pending; D3 rows_lane_store_bindings_missing; D4 gf1_real_dense_manifest_missing; 16a Gloo blocked in sandbox only.
- RESULT 20261117T0501Z_RESULT_build7.md (carries a QUESTION: in-forward reader hook for EAT A2-A4 stays out of build 8 by default).

## Build 7 prompt contents (W/prompts/build7.md, items 1-19 incl. 16a; inputs in W/work/design/)
1-5 ORCH 1124Z D1-D4 + empty remove_files; 6 ORCH 1127Z pinned max/min_pixels and trainable list; 7-10 ORCH 1147Z scale-head loss, frozen response format, guard-only rows check, claim label; 11 ORCH 1155Z USER rulings (frame count 32/64 parameter incl. EAT-1's hard-coded sites, no answer-side unit conversion, ReVSI first, SFT first); 12 ORCH 1234Z both-path mix + ORCH 1250Z b08 `both` policy and type gate (spec PARTB_PREP_b08.md c32ca00c); 13 ORCH 1307Z R0 exclusion (R0_SCENES.json f7c45817 fetched from trinity-1-18 b10_reserve, sha verified; R0_ROOMS bdb5d402; R0_census.py); 14 ORCH 1300Z/1325Z GF-1 cache patch 3610e972; 15 ORCH 1318Z/1504Z/1527Z EAT-1 findings: export manifest with G3T tower weights, fix-or-register A3/A4 items, CPU EAT-1 run (code and reports from trinity-3-30 b03_e2etest in W/work/design/eat1_b03), portrait-stretch audit; 16 ORCH 1342Z h1_headsft faithful own-value rows patch cdc6c9f7 (W/inbox/h1_faithful_fix_b5_1620Z, supersedes bd0fd6bb; review verdict copy W/work/design/h1_faithful/REVIEW_VERDICT_H1KIT.md); 16a ORCH 1909Z USR1 stop defect (find why ranks ignore the stop file, fix, CPU proof with gloo ranks, keep stop_after_step + export fallback); 17 suites; 18 restage kits; 19 build 6 leftovers (finish its qualification on build 7's final tree; package runner resumes finished groups).

## Done by tree_rebuild4 Devin session 4 (03:48Z-09:04Z)
- Polled build 8 every 10 min to 09:03Z; RESULT rotate 0903Z.
- 06:55Z ORCH ANSWER recovery_gate: plan accepted; admit simulated statuses, report them separately, prefer real statuses where the rows lane has them; ONE review of build 9's gate change (it touches admission) — request it in the build 9 RESULT. Folded into build9_draft.md.
- 06:47Z ORCH NOTE recovery_rows_required read; found the build 7 row-text gate refuses 1532/1532 a0_recovery rows (W/work/lane_stop/RECOVERY_GATE_CHECK.json, copied to W/work/design/ with the note); RESULT 0649Z; build9_draft.md written.
- Polled build 7 to its end; verified seal 26a635fc; mirrored package; RESULT 0501Z build7; Gloo check outside sandbox (pass); wrote W/prompts/build8.md and dispatched build 8 05:02Z; design record + INDEX updated to build 7. One tssh call (mirror). No GPU, Orchard, Git or deletion.

## Done by tree_rebuild4 Devin session 3 (22:18Z-03:46Z)
- Polled build 6 to its end; verified seal; mirrored the b6 package to trinity-1-18; filled item 19 in build7.md; dispatched build 7 23:16Z; RESULT build6_end_build7_started; polled build 7 every 10 min (poll2.sh now prints suite group progress); RESULT rotate 0346Z. One tssh call (mirror). No GPU, Orchard, Git or deletion.

## Done by tree_rebuild4 Devin session 2 (18:08Z-22:15Z)
- Polled build 6; recorded ORCH 1844Z no-GPU order (lane has no GPU job); folded ORCH 1909Z USR1 stop defect into build7_draft.md and build7.md as item 16a (copy W/work/design/20261116T1909Z_ORCH_NOTE_usr1_defect.md); rechecked build 7 inputs (gf1 3610e972 both copies, h1 cdc6c9f7, R0_SCENES f7c45817); pre-verified seal 427fb3cb and package sha; prepared W/prompts/build7.md. No ssh, GPU, Orchard, Git or deletion.

## Done by tree_rebuild4 (Devin, 12:23Z-18:00Z)
- RESULT 1227Z checkpoint (before ORCH 1228Z withdrew the order). Folded ORCH 1155Z-1527Z and the h1 patch into the build 7 prompt (list above). Fetched from other nodes with tssh: R0_SCENES.json and census.py (trinity-1-18), eat1 code + BASELINE_A2_TREE.md, EAT1_READY.md, RUN.md, SCOPE_READ.txt (trinity-3-30). No GPU, Orchard, Git or deletion.

## Done by tree_rebuild3 (06:12Z-11:34Z)
- RESULTs 0618Z build5_progress_and_units, 1026Z build5, 1031Z build6_started, 1134Z rotate; QUESTION 0619Z square_feet_rows -> ORCH 0620Z ANSWER (folded into build6.md item 6).
- Unit rows: 2.871/step (1536/535) in routing (W/out/MIX_A0.json); 10,945 admitted (slices_final/COUNTS_A0_v4.json); all abs-distance programs with one written conversion line; slice: feet 689, inches 678, cm 633; no ft2.
- Build 5 ended 10:21Z exit 0: seal ba346bd9 (855) verified by me; suite 2,185 run / 1,645 passed / 474 pre-existing failure events (base fails the same 395 cases, 14+460) / 0 regressions; R2 343/343; coverage 3,693 observed, 73 frame-host, 3 GPU, 0 CPU gaps.
- Contracts dry run in a copy refused (W/work/contracts_r6/OPERATOR_DRYRUN.log); per-file precheck W/work/contracts_r6/OPERATOR_PRECHECK_R6.tsv. W/work/contracts_r6/tree_copy is an operator scratch copy (removal candidate).
- Design record NEXT_LEG_TREE_REBUILD_20261115.md header and its INDEX.md line updated to build 5 / build 6.

## Identities
- Base: candidate A, seal b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 (792 files) = the source of kit 07ca49df / run 469ddece = /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar (845b1789). The seals 38917ea5 and 37845077 belong to earlier trees. Accepted at ORCH 1819Z. Read-only copy: W/work/base/tree_b01ce449 (also O).
- Tree seals: b1 fab2eea8 (807 files), b2 cd82c5c4 (825), b3 a1f559e2 (838; reviewed NOT READY by review_tree, events/review_tree/REVIEW_VERDICT_TREE.md, copy W/work/review1), b3b ba0c6ebf (841), b4 0fc11a63209cc6e73827149a78dea070aa72f279ec3ed7f79d8d3777be3f4320 (846; build 5's start), b5 ba346bd9e8ba41ed0cd77fea5ae494df544b959ff9f80731f83d761f51a32343 (855; recomputed by tree_rebuild3 10:25Z; build 6's start).
- Packages and mirrors: O/out/tree_rebuild_b3_a1f559e2.tar (39b2b5db…) and O/out/tree_rebuild_b3b_ba0c6ebf.tar (aa75d294…), both mirrored at trinity-1-13:/scratch/jjyeung/n30_mirror/tree_rebuild/ (sha equal). No package of b4. Build 5: W/out/tree_rebuild_b5_ba346bd9.tar (84,500,480 B, sha256 bc31a06dd37e742dbf8bad493cbe5d90c18b2bf1dbb6b9f7ef992137a0b33726), mirrored at trinity-1-18:/scratch/jjyeung/n30_mirror/tree_rebuild/ (sha equal, 10:26Z). Build 5 kits W/work/build5/kits/a0 8cdda797..., a2 58a9b42e... (GO=false).
- Pinned shared inputs (W/work/shared, W/work/rows_slices): validator a41ba19190eb354168ce5837b2047fb6510c868c5d7cbfbf160cbe924777e268 (rows_rebuild final; tests cab38fe6); WITHHELD_ROOMS_80.json 634820b4…; merged dev list dev_scene_exclusions_d0.json a1869ae28f6d3f1815993da776f4c4798f67bad4c555c3bb80cc48fcecb23af5 (bound byte for byte; the tree's own derivation 184fcda3 differs only in keying: O/out/MERGED_LIST_COMPARE.txt). Slices slices_v3 (D0 v3 + A0 v3) and slices_final (A0 v4) from trinity-1-13 rows_rebuild.
- Init: step-544 artifact 1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef; an exact resume of 469ddece refuses, and a warm start under a new identity is the path.

## Rulings in force (events)
- ORCH 1848Z: rows_rebuild draws the single withheld list; camera/pose/pointing metadata are proved in the Orchard frame-host job.
- ORCH 1915Z: keep the routing-opener rows on a warm start (config switch, witness); cont_ops: launch_s1/build.py cannot rebuild four-stream kits, so the four-stream case is first-class.
- D0 ruling 1844Z, applied to A0: route planning is direct in the VQA store; routing carries programs only (out/MIX_A0.md).
- ORCH 2018Z: the 80 withheld rooms are out of every A0 stream, with all bindings consistent (build 3b + a1869ae2).
- ORCH 2233Z/2339Z: O cap 5 GB; 3-30 floor 200 GiB; future builds overwrite fixed proof folders in place; real-row outputs are counts + hashes + at most 200 examples.
- ORCH 0022Z: the second review comes only after the full suite completes with zero CPU gaps; the frame-host job needs GO with its packet.
- ORCH 1844Z (USER): no GPU use anywhere, no Orchard submission (general included) until the orchestrator says GPUs are back; this lane runs no GPU job (build 6 is CPU only).
- Defaults in force (orchestrator header): claim scope VSI-Bench, VSTI, ReVSI; the 27 qualification rooms do not bind; 3D box keeps one Locate line; no replay from Devin logs; GF-1 schedule 400 adapter-only + 600 full steps (build default).

## Open
- 14 evidence records must be regenerated (W/out/RECORDS_TO_REGENERATE.md); the kits refuse at init_m544 until they exist; build 6 states which ones T2 changes.
- Design record /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_TREE_REBUILD_20261115.md (+INDEX line); update it at the next RESULT.
- REMOVAL_CANDIDATES.md in O lists about 2.4 GB of temporaries and proof outputs for the user.

## Rules reminders
- Builds go to Codex only: `(cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement W <prompt> --model gpt-6-astra --effort high --label tree_rebuildN --skip-git-check)`, run in tmux. Each prompt restates the "Rules for the build" (copy lines 5-17 of W/prompts/build8.md).
- Fewer than 2 ssh calls into Trinity per minute, each with timeout and -o ConnectTimeout=20. No Git, no deletion, no GPU, no Orchard submission without GO. Events at most 20 lines.
