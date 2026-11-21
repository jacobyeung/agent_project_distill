W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; A=$W/w24z11b/a_zffhb1q8
grep -n -i 'upload\|install\|X/n\|n_go\|destination\|orchard' $W/w24z11b/out/ARM_LAUNCH_24M4Z11B.md | cut -c1-300 | head -40
python3 - <<'PY'
import json
for f in ('UPLOADS_ARMED.json','UPLOADS_ARMED_GO.json'):
  d=json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24z11b/a_zffhb1q8/'+f))
  print(f, [k for k in d])
  for x in d['files']: print(' ',x.get('action'),x['name'],x.get('destination'),x['bytes'],x['sha256'][:8],(x.get('baseline_sha256') or '')[:8])
  for k in d:
    if k not in ('files','already_staged'): print(' ',k,str(d[k])[:300])
PY
du -sh $A/armed/kits/* $A/armed/upload/*; find $A/armed/upload -type f | head -30
