S='/scratch/jjyeung/orch_n30/fb_pack2/STATUS.md'; t=open(S).read(); new=open('/scratch/jjyeung/orch_n30/fb_pack2/work/running.md').read()
a=t.index('## Running at'); b=t.index('## Open questions')
t=t[:a]+new+'\n'+t[b:]
t=t.replace('| Patch A (subset','| Patch A [GO AFTER FIXES: MUST1 legacy behaviour, MUST2 camera pin; fix = patchA2] (subset')
t=t.replace('| Relcnt v1 |','| Relcnt v2 | F1/relcnt2/out (3,600 rows, cap 0.60, tar fbp_relcnt2.tar) | LOO mean 57.6%, pair 49.7% | fbp_relrev2 RUNNING (next boundary) |\n| Relcnt v1 |',1)
t=t.replace('- QUESTION 2107Z: pointing eval prefill (default record mismatch); prior2b default resume with copied inputs.','- QUESTION 2107Z: answered by RULING 2109Z (pointing out of the first boundary; prior default stands).\n- RESULT 2116Z default: prior binds only if prove_on_prepared.py passes on N\'s real prepared receipts before the boundary.')
t=t.replace('fbp_relcnt2 (1-18).','fbp_relcnt2 (1-18); fbp_patchA2, fbp_prior2b (2-28, fb_pack2). Cursor: fbp_relrev2 (1-18, fb_pack2).')
open(S,'w').write(t)
