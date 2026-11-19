S='/scratch/jjyeung/orch_n30/fb_pack2/STATUS.md'; t=open(S).read()
a=t.index('## Running at'); b=t.index('## Next (in order)')
t=t[:a]+'''## Running at 21:57Z (all on 2-28)
- Codex fbp_patchA2 (F2/patchA2, 21:15Z; prompt fb_pack2/work/prompts/fbp_patchA2_full.md 4b289bfe): patchArev MUST 1+2; finishing full suites at 21:52Z. Then Cursor confirm review (F2/patchA2rev).
- Codex fbp_camform2 (F2/camform2, 21:56Z, due ~23:00Z; fbp_camform2_full.md bd0cdda8): camformrev M1 (refuse field when deferred), S1 byte-compare policy 169c439a, S2 changed-line counts; patch vs base+PATCH_A and vs base+PATCH_A2. Then Cursor confirm review; GO by 03:00Z; exposure counts from post-launch Orchard job (ANSWER 2133Z) by 06:00Z.
- Codex fbp_pointD (F2/pointD): resumed 21:53Z (lowest priority preparation, RULING 2109Z).
- Cursor fbp_donor2rev (F2/donor2rev, 21:56Z; PROMPT 42efb058): confirm review of donor2 (incl. donor prepare->ckpt->resume test).
- Cursor fbp_priorrev (F2/priorrev, 21:56Z; PROMPT d1519392): review of PATCH_PRIOR + prior2b proof + prove_on_prepared.py.
- Done, not yet used: Cursor fbp_pointrec RECORD.md (F2/pointrec) -> read, then distill_design/POINTING_TRACE_FORM_20261119.md + INDEX line.

'''+t[b:]
t=t.replace('| Donor patch [donorrev GO AFTER FIXES M1-M3 + S1 prep receipt; fix = donor2] |','| Donor patch [donorrev GO AFTER FIXES; fix = donor2: F2/donor2/out PATCH_DONOR2.patch (8 files vs 57a1f14d) + DELTA, READER_REQUEST.md, REAL_WEIGHT_COMMAND.sh, S1 documented: boundary prepares afresh with donor; donor2rev RUNNING] |')
t=t.replace('| Prior patch |','| Prior patch [prior2b F2/prior2b/out: Trinity-side proof complete, NO_GO only for training-host native offsets (pointing, pose, routing_base) -> run out/prove_on_prepared.py on N real receipts (HOST_INPUTS.json); priorrev RUNNING] |')
t=t.replace('| Patch C camform |','| Patch C camform [camformrev GO AFTER FIXES: M1 deferred-mode silent ignore; fix = camform2] |')
open(S,'w').write(t)
