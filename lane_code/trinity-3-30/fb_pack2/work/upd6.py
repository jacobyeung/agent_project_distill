S='/scratch/jjyeung/orch_n30/fb_pack2/STATUS.md'; t=open(S).read()
a=t.index('## Running at'); b=t.index('## Next (in order)')
t=t[:a]+'''## Running at 22:25Z (all on 2-28)
- Codex fbp_camform2 (F2/camform2, 21:56Z, due ~23:00Z; fbp_camform2_full.md bd0cdda8): camformrev M1/S1/S2; patch vs base+PATCH_A and vs base+PATCH_A2. Then Cursor confirm review (F2/camform2rev); GO by 03:00Z; exposure counts from post-launch Orchard job (ANSWER 2133Z) by 06:00Z.
- Codex fbp_donor3 (F2/donor3, 22:22Z, ~1 h; fbp_donor3_full.md 97e5a677): donor2rev M4 (reader recipe: strict-load + freeze private visual before attach; runtime test with the real CarrierC1). Then a short confirm review (F2/donor3rev).
- Codex fbp_pointD (F2/pointD): resumed 21:53Z (lowest priority).
- Cursor fbp_patchA2rev (F2/patchA2rev, 22:22Z; PROMPT 1405eeb0): confirm review of PATCH_A2 3ecd924f.
- QUEUED for next free Codex slot: fbp_prior2c = fix prove_on_prepared.py per F2/priorrev/REVIEW_VERDICT.md MUST 1 (check production binding direction_prior, offsets equal recomputed, run enabled plan on production binding), MUST 2 (anchor real mode to N store hashes/source pins/sealed tree), SHOULD 3 (final receipt <root>/b/receipt.json). Preparation only (prior -> second boundary unless discovery run gives offsets, ANSWER 2202Z).

'''+t[b:]
t=t.replace('| Donor patch [donorrev GO AFTER FIXES; fix = donor2:','| Donor patch [donor2rev GO AFTER FIXES M4 reader recipe only -> donor3; donorrev fixes in donor2:')
t=t.replace('donor2rev RUNNING] |','] |')
t=t.replace('| Patch A [GO AFTER FIXES: MUST1 legacy behaviour, MUST2 camera pin; fix = patchA2]','| Patch A [superseded by PATCH_A2: F2/patchA2/out PATCH_A2.patch 3ecd924f (11 files vs 57a1f14d), DELTA a848718c, tar 76709467; camera pin e8cbda99; fuzz 0 on 189df6ac; patchA2rev RUNNING]')
t=t.replace('priorrev RUNNING] |','priorrev: sampler GO; checker GO AFTER FIXES -> prior2c queued; prior -> second boundary unless discovery-run offsets] |')
t=t.replace('## Delivered','''- ORDER 2202Z (pointing K1): done. BLOCKER 2215Z + RESULT 2219Z in events/tree_rebuild and fb_pack: admission admits the 320 K1-heldout pointing rows (no room audit on pointing; 12 remove lists match 0); fix list F1+F2 /scratch/jjyeung/orch_n30/fb_pack/k1point/REMOVE_POINTING_K1_HELDOUT.jsonl d21e374f (320 rows), AUDIT_POINTING_K1.json 8d5c1a9a, audit_point.py 6035517f (= fb_pack2/work/audit_point.py); with list: 0 K1-heldout kept, 18,116 before shape filter. Pose + routing base: CANNOT CHECK (no Trinity copy). Disclosure line added to STORE_V7_ROOM_AUDIT and POINTING_TRACE_FORM records. Prior -> second boundary unless discovery-run offsets.

## Delivered''',1)
open(S,'w').write(t)
