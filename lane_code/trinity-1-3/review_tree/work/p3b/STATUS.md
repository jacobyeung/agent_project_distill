# tree_rebuild STATUS (trinity-3-30; lane /scratch/jjyeung/orch_n30/tree_rebuild)
Updated: 2026-11-15T21:50Z

## Done
- Step 1 base verified: candidate A tree seal b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 (792 files) = recorded source seal of kit 07ca49df / run 469ddece; equals /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar (sha256 845b1789…) member by member. Not 38917ea5 (tree_s1_nf) nor 37845077 (importfix). Event 20261115T1817Z_RESULT_base_verified.md. Accepted by ORCH 18:19Z (no Orchard comparison needed). The plan's seal names 38917ea5 and 37845077 are earlier trees (their tars sit in /data3/jjyeung/distill_src_archive/); the sealed kit 07ca49df ran b01ce449.
- Base read-only at work/base/tree_b01ce449; build copy work/tree_r1; per-file list out/BASE_FILES_b01ce449.sha256.
- Inputs in lane: recovered texts work/rec/recovered (tar sha 29bce35b…), exclusion records work/records/* (out/EXCLUSION_RECORDS.sha256), design records work/records/design (out/DESIGN_RECORDS.sha256), /data3 source tar work/t_b01ce449beffe35b.tar.

## Running
- Build 3b (ORCH 2018Z: withheld rooms out of every A0 stream; merged dev list bound at config + s1_exclusions totals()/census + s1_routing pool upstream; pool selection, census and stream receipts re-derived in the frame-host job): tmux tree_rebuild_b3b, receipt codex_runs/20261115T214809Z_tree_rebuild3b, prompt prompts/build3b.md. Started 21:48Z. QUESTION 2147Z asks that the review start on the 3b seal (default).

## Done (builds)
- Build 3 20:02-21:21Z: seal a1f559e2… (838 files); kits A0 work/build3/kits/5c2ca33ca02a (9057919d…), A2 work/build3/kits/473395544605 (6737fcc9…); report out/BUILD3_REPORT.md; card out/PRELAUNCH_CARD.md; frame-host job out/FRAME_HOST_JOB.md (not run). Package out/tree_rebuild_b3_a1f559e2.tar (39b2b5db…), mirrored at trinity-1-13:/scratch/jjyeung/n30_mirror/tree_rebuild/ (sha equal). Design record /data2/.../distill_design/NEXT_LEG_TREE_REBUILD_20261115.md + INDEX line.
- Build 2 19:16-20:00Z: seal cd82c5c4… (825 files), snapshot out/tree_r1_build2_cd82c5c4.tar (454a4005…), report out/BUILD2_REPORT.md, event RESULT build2. Kits inspection-only (fixed in build 3).
- Build 1 (items 1-5) 18:25-19:16Z: tree seal fab2eea8… (807 files), snapshot out/tree_r1_build1_fab2eea8.tar (411e9329…), report out/BUILD1_REPORT.md, event 1917Z RESULT build1.
- Shared inputs copied to work/shared (out/SHARED_INPUTS.sha256): trace_grammar.py 49e814eb, WITHHELD_ROOMS_80.json 634820b4; sealed kit 07ca49df metadata at work/kit07ca49df_meta/m (from rows_rebuild).

## Open
- Real-row proof: waiting for rows_rebuild slices (<=2,000 rows/family + count file) -> copy to work/rows_slices, run work/build1/REAL_ROW_PROOF.sh.
- Contract patches: waiting for the review_contracts verdict -> copy to work/contracts, run work/build3/APPLY_CONTRACT_PATCHES.sh (small Codex build if anything breaks).
- 14 evidence records must be regenerated (out/RECORDS_TO_REGENERATE.md); kits refuse at init_m544 until then.
- Frame-host job on Orchard needs the orchestrator's GO.

## Next
- Review round 1 (ordered by the orchestrator), then fixes (Codex), then review round 2. Then the real-row proof, the contract patches and the frame-host job when their inputs and GO arrive.
