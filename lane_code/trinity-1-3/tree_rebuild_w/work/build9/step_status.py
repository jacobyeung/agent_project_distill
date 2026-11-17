"""Record a completed build step with its evidence."""
import json,sys
from pathlib import Path
B=Path(__file__).resolve().parent
step=sys.argv[1]
if step=='1':
 p=B/'proofs/regressions';r=json.loads((p/'results.json').read_text())
 failures=r['failures']+r['errors']
 assert r['complete'] and len(failures)==1 and failures[0][0]=='tests.test_gf1_cache.CachedBank.test_parity_cached_vs_online'
 parity=json.loads((p/'BF16_PARITY.json').read_text())
 result=dict(status='blocked',blocker='BF16_CACHE_GRADIENT_PARITY',fixed_fixtures=r['passed'],
     parity_source='work/build9/proofs/regressions/BF16_PARITY.json',
     reason='Lossy BF16 storage of FP32 pooled normalized features adds quantization before the FP32 affine/projection. The same BF16 tower/base with FP32 cache passes. No cast-order defect was found; the original tolerance and kit refusal remain.',
     source_sites=['student_pilot/gf1_cache.py:42','student_pilot/gf1_cache.py:132','student_pilot/gf1.py:99','student_pilot/gf1.py:118'])
 (p/'DISPOSITION.json').write_text(json.dumps(result,indent=2)+'\n')
 text='Step 1: fixture regressions pass; BF16_CACHE_GRADIENT_PARITY remains blocked at its original tolerance. Evidence: `work/build9/proofs/regressions/DISPOSITION.json` and `BF16_PARITY.json`.'
elif step=='2':
 r=json.loads((B/'proofs/r2/results.json').read_text())
 assert r['complete'] and not r['failures'] and not r['errors']
 text=f"Step 2: R2 passes {r['tests']} executions with no failures or errors (`work/build9/proofs/r2/results.json`)."
else:text='Step '+step+': '+' '.join(sys.argv[2:])
with (B/'STATUS.md').open('a') as f:f.write('\n'+text+'\n')
print(text)
