# tree_rebuild STATUS (successor resumes from this file alone)
Updated: 2026-11-16T10:56Z by tree_rebuild3 (session 06:12Z-12:12Z). Lane W = trinity-1-3:/scratch/jjyeung/orch_n30/tree_rebuild_w (cap 8 GB; 1.2 GB at 10:30Z). O = trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild holds builds 1-4 history (3.95 of 5 GB; do not grow).
Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/ (read every *_ORCH_* file there and W/inbox at each step). Poll helper: W/poll.sh (edit the receipt path for build 6).

## Running now
- Build 6 (Codex gpt-6-astra high) in tmux `tree_rebuild_b6` on trinity-1-3, started 10:30Z, working in W. Prompt W/prompts/build6.md. Receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T103023Z_tree_rebuild6 (final_message.md + meta.json at the end). Codex status W/work/build6/STATUS.md; report W/out/BUILD6_REPORT.md; package W/out/tree_rebuild_b6_<seal8>.tar. Build 5 took 10 h; expect several hours.
- Scope: contracts r6 (exact patches for 32 files at base; three-way merge + per-hunk table for carrier_c1_routing.py fe95f5b6, carrier_c1_run.py 91fd662a, ground_rows.py 86e2a0b7; W/work/contracts_r6/OPERATOR_PRECHECK_R6.tsv), packet suite 202, full package suite, coverage (zero CPU gaps), OFF/ON row proofs, kits A0/A2 under W/work/build6/kits, ORCH 0602Z T1-T5 (T2: init as one pinned input, unchosen), ORCH 0620Z square feet (no room family; ft2 + inches valid direct units; count room rows asked in ft2; per-unit score breakdown metres first), MIX_A0.md 22,280 -> 10,945, build 5 leftovers.
- Packet script dry run refused (OPERATOR_DRYRUN.log: read-only artifacts/, then carrier_c1_routing.py hash); hence the merge build. Packet copy in W/work/contracts_r6 (hashes verified 10:2xZ); design record copy W/work/design/.

- 10:50Z build 6 reported packet-suite support fixtures absent (its STATUS.md). 10:55Z I added W/work/contracts_r6/packet_root (90 MB, contracts_rebuild layout of every support file the 17 tests read; README_PACKET_ROOT.md). If build 6 ends without the 202-test run, the fix build runs it from packet_root.

## When build 6 ends
1. Read final_message.md and W/out/BUILD6_REPORT.md (never the whole transcript). Recompute the seal: `cd W/work/tree_r1 && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"`.
2. Mirror the package: `cat pkg | ssh -o ConnectTimeout=20 trinity-1-18.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild/<pkg> && sha256sum ...'`; compare sha256.
3. RESULT event build6 (<=20 lines): both suites' counts, coverage classes, per-hunk merge summary, unit rows per step and per unit, ft2 room-row count. If the full suite completed and zero CPU-reachable gaps remain, ask ONCE for the second review of the integrated tree (ORCH 0022Z/0308Z; Devin Opus high refute; review_tree did round 1). Otherwise one more Codex fix build with the same rules.
4. The frame-host CPU job on Orchard needs the orchestrator's GO with its packet; never submit without it.

## Done this session (tree_rebuild3)
- 06:18Z RESULT build5_progress_and_units; 06:19Z QUESTION square_feet_rows -> ORCH 0620Z ANSWER (ruling folded into build6.md item 6).
- Unit rows: 2.871/step (1536/535) in routing (W/out/MIX_A0.json); 10,945 admitted (slices_final/COUNTS_A0_v4.json); all abs-distance programs with one written conversion line; slice: feet 689, inches 678, cm 633; no ft2.
- 10:26Z RESULT build5: ended 10:21Z exit 0; suite 2,185 run / 1,645 passed / 474 pre-existing failure events (base fails the same 395 cases, 14+460) / 0 regressions; R2 343/343; coverage 3,693 observed, 73 frame-host, 3 GPU, 0 CPU gaps.
- 10:31Z RESULT build6_started.

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
- Defaults in force (orchestrator header): claim scope VSI-Bench, VSTI, ReVSI; the 27 qualification rooms do not bind; 3D box keeps one Locate line; no replay from Devin logs; GF-1 schedule 400 adapter-only + 600 full steps (build default).

## Open
- 14 evidence records must be regenerated (W/out/RECORDS_TO_REGENERATE.md); the kits refuse at init_m544 until they exist; build 6 states which ones T2 changes.
- Design record /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_TREE_REBUILD_20261115.md (+INDEX line); update it at the next RESULT.
- REMOVAL_CANDIDATES.md in O lists about 2.4 GB of temporaries and proof outputs for the user.

## Rules reminders
- Builds go to Codex only: `(cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement W <prompt> --model gpt-6-astra --effort high --label tree_rebuildN --skip-git-check)`, run in tmux. Each prompt restates the "Rules for the build" (O/prompts/rules_block.md; replace the path with W).
- Fewer than 2 ssh calls into Trinity per minute, each with timeout and -o ConnectTimeout=20. No Git, no deletion, no GPU, no Orchard submission without GO. Events at most 20 lines.
