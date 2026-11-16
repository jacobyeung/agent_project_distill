import json,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[2]
for f in ['own_probe/out/EVAL_ROOMS.json','revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json']:
 d=json.loads((R/f).read_text());print(f)
 for k,v in d.items():
  if isinstance(v,dict):print(k,len(v),list(v.items())[:2])
  elif isinstance(v,list):print(k,len(v),v[:2])
samples={}
for p in sorted((R/'dose_pool/out/POOL_S1').glob('*_admitted.jsonl.gz')):
 with gzip.open(p,'rt') as f:
  for line in f:
   r=json.loads(line)
   if r.get('type') not in ('object_abs_distance','room_size_estimation'):continue
   key=(r['canonical'].split('/')[0],r['type'])
   if key not in samples:
    samples[key]=r;print('ROW',p.name, json.dumps({k:v for k,v in r.items() if k not in ['suffix','events','mdg_gate_token_positions']})[:6500])
print('sample types',list(samples))
