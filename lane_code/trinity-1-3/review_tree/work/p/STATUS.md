# tree_rebuild STATUS (trinity-3-30; lane /scratch/jjyeung/orch_n30/tree_rebuild)
Updated: 2026-11-15T20:05Z

## Done
- Step 1 base verified: candidate A tree seal b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99 (792 files) = recorded source seal of kit 07ca49df / run 469ddece; equals /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar (sha256 845b1789…) member by member. Not 38917ea5 (tree_s1_nf) nor 37845077 (importfix). Event 20261115T1817Z_RESULT_base_verified.md. Accepted by ORCH 18:19Z (no Orchard comparison needed). The plan's seal names 38917ea5 and 37845077 are earlier trees (their tars sit in /data3/jjyeung/distill_src_archive/); the sealed kit 07ca49df ran b01ce449.
- Base read-only at work/base/tree_b01ce449; build copy work/tree_r1; per-file list out/BASE_FILES_b01ce449.sha256.
- Inputs in lane: recovered texts work/rec/recovered (tar sha 29bce35b…), exclusion records work/records/* (out/EXCLUSION_RECORDS.sha256), design records work/records/design (out/DESIGN_RECORDS.sha256), /data3 source tar work/t_b01ce449beffe35b.tar.

## Running
- Build 3 (F executable kits, G scope gate on all entrypoints, A opener rows, B four-stream, C m544 layout, D contract patches if present, E real rows if present, 11 frame-host job, 12 card): tmux tree_rebuild_b3, receipt /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20261115T200209Z_tree_rebuild3, prompt prompts/build3_final.md. Started 20:02Z. Fresh work/tmp; builds 1-2 temp kept in work/tmp_b1b2.

## Done (builds)
- Build 2 19:16-20:00Z: seal cd82c5c4… (825 files), snapshot out/tree_r1_build2_cd82c5c4.tar (454a4005…), report out/BUILD2_REPORT.md, event RESULT build2. Kits inspection-only (fixed in build 3).
- Build 1 (items 1-5) 18:25-19:16Z: tree seal fab2eea8… (807 files), snapshot out/tree_r1_build1_fab2eea8.tar (411e9329…), report out/BUILD1_REPORT.md, event 1917Z RESULT build1.
- Shared inputs copied to work/shared (out/SHARED_INPUTS.sha256): trace_grammar.py 49e814eb, WITHHELD_ROOMS_80.json 634820b4; sealed kit 07ca49df metadata at work/kit07ca49df_meta/m (from rows_rebuild).

## Open
- Waiting on: rows_rebuild per-family slices of at most 2,000 rows plus a count file (ORCH 18:48Z agreed; they come after D0), contracts_rebuild PATCH_*_r2.diff.
- Camera, pose and pointing metadata get their proof in build 3's Orchard frame-host job (ORCH 18:48Z).

## Next
- Read build 1 report; then build 2 (policy, withheld rooms, kit, two configs, mix), build 3 (frame-host job, card), then RESULT asking for review.
