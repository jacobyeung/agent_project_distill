# Frame-host inputs of kits A0 8cdda797 and A2 58a9b42e (build 5): why GO=false, and each input qualified (rows_a2, 2026-11-16 ~11:25Z)

Method: decoded each kit's config (A0 k/3f437bca…, A2 k/8d48d580…), staging plan (k/0.json -> A0 k/ba552d64…, A2 k/1c02f9e6…) and GO record (k/4.json);
checked every u/ pin of the config against its staging entry (sha256), the 34 inline payloads locally, and the archives and members on Orchard
(3 ossh calls; outputs work/orch_q{1,2,5}.out; table work/KIT_INPUT_QUALIFICATION.json; parent staging work/parent_k0.json from the sealed kit 07ca49df k/0.json).

## Why GO=false
k/4.json in both kits: go=false, admission=false, production_go_granted=false, allow_until 1970. The kit RESULTS name four blockers: component evidence
(the 14 records to regenerate), post-filter counts, host admission (the frame-host job has not run), independent review. Those are by design: no kit is
admitting until the frame-host job and review pass. My audit finds four further defects that would stop the frame-host job at item 2 (physical staging)
or train the wrong rows:

| # | Defect | Kits | Evidence | What closes it |
|---|---|---|---|---|
| D1 | 19 staging entries name archive okit/in/e00 (83 MB, 58 members) for members it does not hold: the 13 eb3429c5 pool shards, k/frame_map, k/frame_plan, k/input_source_tokenizer, the vxm_m4 VQA receipt, the 7c9f2d84 pointing receipt (+ A2's dense manifest). Only the 2 e84d901c/z members (bank 986ba20f.npz, training_scenes eb035f92.json) are in e00 and match. | A0, A2 | orch_q2.out (ABSENT x19), orch_q3.out (e00 listing) | Point each entry at its real source, all verified on Orchard today by sha256: /home/jjyeung/okit/i/eb3429c5/eb3429c5.tar (f0e71513…, holds the 13 shards per parent inventory); /home/jjyeung/okit/x/07ca49df/k/{frame_map.jsonl.gz 17aa3e9e…, frame_plan.json.gz 7cc01f36…, input_source_tokenizer.json 5f9e4d49…}; okit/in/cr/524b14f9f180.p00 (vxm_m4 receipt 524b14f9…); /project/community/jjyeung/okh7/7c9f2d84/receipt.json (93b21a3a…). Tree fix (staging plan builder) |
| D2 | The init artifact u/1d6eeb28… is staged from /tmp/jjyeung/in/1d6eeb28… (an operator-local path); it does not exist on Orchard. | A0, A2 | orch_q2.out / orch_q5.out MISSING | Bind the step-544 export's real location (GCS q8 or Orchard) by sha 1d6eeb28; or the D0 export chosen under NEXT_LEG_INIT_RULE_20261116 |
| D3 | streams/vqa and streams/routing bind the SEALED parent stores (vxm_m4 receipt 524b14f9; r16 receipt 9a7f3310), not D0 v5 / the A2 VQA store, and no A0 family (units, recovery, room, ft²) is staged. The kits would train the sealed rows. | A0, A2 | cfg streams; grep for 4af43b40, e31b18bf, slices: 0 hits | Bind the A2 VQA store (r.sqlite + receipt) and the A0/A2 family files once admitted and uploaded |
| D4 | A2's r2_dense_manifest is the 1-clip synthetic fixture (c1281b1b…, member path on trinity-1-3 /scratch, dense_fixture=true). | A2 | a2 staging; kits/dense.json | The GF-1 dense manifest built on Orchard (DENSE_FRAMES_PLAN option a); not a rows task |

## Qualified (sha256 equal to the manifest)
- Inline payload entries: 34/34 per kit. Orchard files: e00 4b66cc24…, cr/rt_b8b60bcef027.tar b8b60bce… (member r16/receipt.json OK), bwrap e3189038…, okh7/i_abab6c81/30c516bf.json d6d6a53a… (rows_inventory), cr/436d1d64673f.p00 fd60ac2f… (depth_init), bank and training_scenes members of e00.
- Not hashed: venv tar (8.1 GB; size 8,105,379,840 recorded).
- remove_files[4] and [5] are the empty file (sha e3b0c442…): legal only if the tree means "no removals"; flag for the tree lane.
