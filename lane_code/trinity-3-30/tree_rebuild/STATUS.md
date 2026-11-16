# tree_rebuild STATUS (successor resumes from this file alone)
Updated: 2026-11-16T00:45Z. Lane moved: the fix round continues on trinity-1-3, /scratch/jjyeung/orch_n30/tree_rebuild_w (call it W). The original lane trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild (call it O) holds builds 1-4 history and packages; 3.95 GB of a 5 GB cap there, do not grow it.
Events: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/ (read every *_ORCH_* file there and W/inbox at each step).

## Running now
- Build 5 (Codex gpt-6-astra high) in tmux `tree_rebuild_b5` on trinity-1-3, started 00:11Z, working in W. Prompt W/prompts/build5.md. Receipt (readable from any node, no ssh needed): /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261116T001148Z_tree_rebuild5 (final_message.md + meta.json appear at the end). Codex status: W/work/build5/STATUS.md; report at end: W/out/BUILD5_REPORT.md.
- Scope: (1) the full suite to completion from the self-contained package (R2 suite zero failures; legacy failures that also occur on the base are pre-existing and reported with their cause); (2) zero CPU-reachable changed-statement gaps (build 4 left 388); (3) sampler reindexing after a late refusal, checkpoint archives inside checkpoint_disk_guard, the frame_map join for 19 reworded abs-distance rows; (4) the frame-host checklist: review items 1 (venv/bwrap, py3.6), 2 (physical u/ pins), 4 (GCS round trip + restore via gcsput), 5 (real bank catalog), 9 (vocabulary witness from the staged m544 export), 11 (native output scan), each a numbered step of b/f.sh with a receipt and a refusal; (5) A0/A2 kits restaged under W/work/build5/kits; package W/out/tree_rebuild_b5_<seal8>.tar.
- At 00:30Z: W 686 MB, 1-3 /scratch 969 GB free; Codex was running the full suite and then the base under the same harness.

## When build 5 ends (successor's next steps)
1. Read final_message.md and W/out/BUILD5_REPORT.md. Recompute the tree seal in W/work/tree_r1 with the tree's own code: `cd W/work/tree_r1 && /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B -c "import sys; sys.path.insert(0,'.'); from student_pilot.source_seal import inventory; from student_pilot.p3_provenance import digest; f=inventory('.'); print(len(f), digest(f))"`.
2. Mirror the package to a second node over IB (`cat pkg | ssh -o ConnectTimeout=20 <node>.ib 'cat > /scratch/jjyeung/n30_mirror/tree_rebuild/<pkg> && sha256sum ...'`; earlier mirrors are on trinity-1-13) and compare sha256.
3. RESULT event build5 (at most 20 lines). Ask for the second review (Devin Opus high, refute; lane review_tree reviewed round 1) ONLY if the full suite completed and no CPU-reachable statement is uncovered (ORCH 0022Z). If not, run one more Codex fix build in W with the same rules (fixed proof folders overwritten in place; real-row outputs counts+hashes+200 examples).
4. The frame-host CPU job on Orchard needs the orchestrator's GO with its packet; never submit without it.
5. Contract patches: wait for review_contracts to accept contracts_rebuild's r4 packet (events/contracts_rebuild, events/review_contracts). Then copy the patches into W/work/contracts and run work/build3/APPLY_CONTRACT_PATCHES.sh (refuses on base-hash mismatch, never applies level_basis); a small Codex build if anything breaks.

## Identities
- Base: candidate A, seal b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 (792 files) = the source of kit 07ca49df / run 469ddece = /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar (845b1789). The seals 38917ea5 and 37845077 belong to earlier trees. Accepted at ORCH 1819Z. Read-only copy: W/work/base/tree_b01ce449 (also O).
- Tree seals: b1 fab2eea8 (807 files), b2 cd82c5c4 (825), b3 a1f559e2 (838; reviewed NOT READY by review_tree, events/review_tree/REVIEW_VERDICT_TREE.md, copy W/work/review1), b3b ba0c6ebf (841), b4 0fc11a63209cc6e73827149a78dea070aa72f279ec3ed7f79d8d3777be3f4320 (846; build 5's start; verified on 1-3 after the copy).
- Packages and mirrors: O/out/tree_rebuild_b3_a1f559e2.tar (39b2b5db…) and O/out/tree_rebuild_b3b_ba0c6ebf.tar (aa75d294…), both mirrored at trinity-1-13:/scratch/jjyeung/n30_mirror/tree_rebuild/ (sha equal). No package of b4 (it is contained in W).
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

## Open, not blocking build 5
- 14 evidence records must be regenerated (O/out/RECORDS_TO_REGENERATE.md); the kits refuse at init_m544 until they exist.
- Design record /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_TREE_REBUILD_20261115.md (+INDEX line); update it at the next RESULT.
- REMOVAL_CANDIDATES.md in O lists about 2.4 GB of temporaries and proof outputs for the user.

## Rules reminders
- Builds go to Codex only: `(cd /home/jjyeung/agent_project_distill && agent/scripts/codex_dispatch.sh implement W <prompt> --model gpt-6-astra --effort high --label tree_rebuildN --skip-git-check)`, run in tmux. Each prompt restates the "Rules for the build" (O/prompts/rules_block.md; replace the path with W).
- Fewer than 2 ssh calls into Trinity per minute, each with timeout and -o ConnectTimeout=20. No Git, no deletion, no GPU, no Orchard submission without GO. Events at most 20 lines.
