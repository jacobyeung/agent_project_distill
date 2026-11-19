S='/scratch/jjyeung/orch_n30/fb_pack2/STATUS.md'; t=open(S).read()
a=t.index('## Running at'); b=t.index('## Next (in order)')
t=t[:a]+'''## Running at 21:26Z (all on 2-28 unless noted)
- Codex fbp_patchA2 (F2/patchA2, 21:15Z, due ~22:45Z; prompt fb_pack2/work/prompts/fbp_patchA2_full.md 4b289bfe): patchArev MUST 1 (legacy = base when no declaration) + MUST 2 (camera pin e8cbda99 = cam/out/rows/camera_wording.jsonl); PATCH_A2 + DELTA; apply/test on live 189df6ac. Then Cursor confirm review (folder F2/patchA2rev).
- Codex fbp_prior2b (F2/prior2b, 21:15Z, due ~00:15Z; fbp_prior2b_full.md e9692772): all-cell proof with 12 copied inputs + out/prove_on_prepared.py for N's real prepared receipts (/scratch/fsw/.../8865619b/...: exist only after N's preparation; not on orchard-login). Paused 21:22-21:23Z by mistake, resumed (codex pid 311364). Then Cursor review; GO by 04:00Z.
- Codex fbp_donor2 (F2/donor2, 21:22Z, due ~23:00Z; fbp_donor2_full.md d75ec340): donorrev M1-M3, S1 (freeze-time lever, else document re-prepare), S2, S3. Then Cursor confirm review (F2/donor2rev).
- Codex fbp_pointD (F2/pointD): PAUSED (SIGSTOP 21:13Z, codex pid 1803846; RULING 2109Z lowest priority). Resume `kill -CONT 1803846 $(pgrep -P 1803846)` when a Codex slot frees.
- Cursor fbp_camformrev (F2/camformrev, 21:25Z, timeout 2 h; PROMPT bd335539 = fb_pack2/work/prompts/fbp_camformrev_PROMPT.md): review of PATCH_CAMFORM (F2/camform/out, tar 9168bd8b, policy 169c439a, field r1_training.camera_trace_form). GO by 03:00Z needed.
- Cursor fbp_pointrec (F2/pointrec, 21:19Z; PROMPT b266178b): draft RECORD.md for distill_design/POINTING_TRACE_FORM_20261119.md (due 11-20 18:00Z); I copy it to distill_design + INDEX line after reading.
- Cursor fbp_relrev2 (1-18 F1/relrev2, 21:16Z): confirm review of relcnt2 (next boundary).

'''+t[b:]
t=t.replace('| Donor patch |','| Donor patch [donorrev GO AFTER FIXES M1-M3 + S1 prep receipt; fix = donor2] |')
t=t.replace('- RESULT 2116Z default:','- QUESTION 2125Z: donor S1 default = freeze-time lever (fbp_donor2), else boundary must re-prepare.\n- RESULT 2116Z default:')
t=t.replace('| Relcnt v2 |','| Patch C camform | F2/camform/out (PATCH_CAMFORM.patch on base+PATCH_A, 4 files, policy configs/r1_camera_trace_form_v1.json 169c439a, field r1_training.camera_trace_form, tar 9168bd8b) | 2,000 rot + 1,996 dir rewritten, 2,004 unchanged; suite 0 new failures; N exposure MISSING (mocked Filters) | fbp_camformrev RUNNING |\n| Relcnt v2 |',1)
open(S,'w').write(t)
