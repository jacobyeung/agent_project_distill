import json,csv,hashlib,collections
from pathlib import Path
from scan_rows import sha
p=Path('out/FRAMEPOOL.json');d=json.loads(p.read_text());cs=d['captures'];ss={s['id']:s for s in d['streams']}
assert len(cs)==146 and len({c['token'] for c in cs})==146
assert len(d['reviewer_memberships_148'])==148
assert all(c['bench_v2_scene_list'] and c['bench_v2_token_list'] for c in cs)
assert d['frame_universe']['frame_count']==290880 and d['frame_universe']['frame_scenes']==4697
assert len(Path('out/FRAMEPOOL_REPORT.md').read_text().splitlines())<=80
for c in cs:
 assert set(c['per_stream_counts'])==set(ss)
 for sid,v in c['per_stream_counts'].items():
  s=ss[sid]
  if s.get('hits') is None:assert v['observed_rows']=='MISSING' and v['full_count']=='MISSING'
  else:assert v['observed_rows']==s['counts'].get(c['token'],0)
  if s['coverage']=='partial':assert v['full_count']=='MISSING'
positive=[s for s in ss.values() if s['kind']=='archived_training_metadata_sample']
assert sum(s['hits'] for s in positive)==1193
assert len({t for s in positive for t in s['counts']})==125
assert all(sum(s['counts'].values())==s['hits'] for s in ss.values() if s.get('hits') is not None)
assert all(not s['counts'] and not s['frame_reference_counts'] for s in d['evaluation']['sets'])
errors=[]
for path,pin in d['inputs'].items():
 if '::' in path:continue
 if not Path(path).is_file():errors.append('missing '+path);continue
 if sha(path)!=pin['sha256']:errors.append('hash mismatch '+path)
assert not errors,errors
print('PASS 146 captures; 148 memberships; 92 streams; 1193 sample hits; hashes; missing-value semantics; report line limit')
Path('out/VALIDATION.json').write_text(json.dumps(dict(command='/usr/bin/python3 work/validate_report.py',inputs={str(p):{'sha256':sha(p)},'out/FRAMEPOOL_REPORT.md':{'sha256':sha('out/FRAMEPOOL_REPORT.md')},'work/verified_hits.json':{'sha256':sha('work/verified_hits.json')}},result='PASS',captures=146,memberships=148,streams=len(ss),observed_sample_hits=1193),indent=2)+'\n')
