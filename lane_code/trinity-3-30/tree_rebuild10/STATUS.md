# tree_rebuild STATUS (successor resumes from this file alone)
Updated: 2026-11-19T00:00Z by tree_rebuild10 (Devin Opus high; session trinity-3-30, work trinity-1-18; started 23:50Z 11-18; rotate by 05:20Z). Predecessor tree_rebuild9 lost with trinity-1-3 (11:29Z); its last STATUS = W/work/STATUS_tree_rebuild9.md.
W = trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w (1.6 GB of 14). Symlink on trinity-1-18: /scratch/jjyeung/orch_n30/tree_rebuild_w -> W (old absolute paths in build 9-14 evidence resolve). Session folder trinity-3-30:/scratch/jjyeung/orch_n30/tree_rebuild10 (scripts, small bundles; 3-30 /scratch 106 GB free: write nothing big there).

## Inventory (step 1, 23:52-00:00Z)
- Lost with trinity-1-3: W/w15 (build 15 run), W/work/{loader_n2, loader_n2/countfix (census_b1.py, CENSUS_B1.json), b13n, conf15}, all build outputs not packaged; r1_pkt/work/derive_7fh23bg8/b/k (P staged copies), rows_rebuild division file 4c230a7e.json (sha 0d28fdd4; not on any mirror per r1_ops6), rows_r1/rows_r2 lane roots (mirrors survive).
- Survives on trinity-1-18: n30_mirror/tree_rebuild/ packages b5..b14 (b14 82684e32 sha verified), n30_mirror/rows_r2/out/vehN_pool_abs_distance_full (repaired aedd3b54 8,315), n30_mirror/rows_r1/out (vehN_units, recovery_v3, a2_vqa_v7 store rows.sqlite 210b2534), n30_mirror/count_diag (COUNT_FIX_EVIDENCE_FINAL tgz), n30_mirror/r1_ops6/cprime_build_32337655.tar. p1cpu env present. 460 GB RAM avail.
- Survives on trinity-3-30: lane-code clone distill_sync/repo/lane_code/trinity-1-3/{tree_rebuild_w (scripts: loader_n census/alloc/plan + JSONs, conf13/s,t11 refute scripts, cont_real, stage51, prompts incl. build15.md), review_treen1, review_tree11}; r1_ops6/cp/out (A a0.json 9fd18816, C operator/c4.json 21528289, C' config.json 31abe087 = identity 774503e2, records n.json 02315a74, z.json caba6a56, c/j/r/v/d); r1_ops6/rec/r1_ops/work (snap_fac07052, snap_6a5c7d00, adm171377 receipts); r1_ops6/cf/final_evidence/COUNT_FIX_REMOVE_B1.jsonl 25c3db82.
- Rebuilt in W: w9f, w12, w13, w14 = fresh untars of mirror packages; w15 = untar b14; W/work, W/prompts = clone copies (lane scripts); W/clone/{tree_rebuild_w,review_treen1,review_tree11}; W/inputs/{p_configs,records,m100}; W/ext/r1_ops/work/{snap_fac07052,snap_6a5c7d00,adm171377(+prepared/receipt.json 49caeb70 read from Orchard 00:03Z)}.
- Orchard 00:03Z: 172660 (C') RUNNING since 22:20:33Z; runs/6ed2c7aa/inputs/prepare_da5580b7d92f490bb3cfe8df447e7820 exists (runtime config not yet read).

## Running
- Codex build 15 (gpt-6-astra high), tmux tr10_b15 on trinity-1-18, dispatched 23:56Z, prompt W/prompts/build15.md (repointed to W/ext; adds C' 31abe087 as third real config), workspace W/w15, log W/work/build15_dispatch.log, receipt codex_runs/*_tree_rebuild15 (newest). Poll every 10 min.

## Next
2. Build 15 ends: seal recompute, sha, mirror (ops_mirror if <100 MB + n30_mirror), confirm: real15 A/C/C' admit, refuse set by name, conf13/s + t11 refute scripts repointed; RESULT build15.
3. Bind rows (build 16 prompt to draft while b15 runs): full distance pool aedd3b54 + merged receipt 2c622905, recovery v3 994, units 8,577, remove n.json + z.json, card counting 10.46/totals 0/freed to direction (C' cells), weight_scale 0.04; producer + composition + loader audit on real stores.
4. Handover file list with r1_ops6 (RESULT in events/r1_ops). 5. Proof QUESTION for GO. 6. One review.
