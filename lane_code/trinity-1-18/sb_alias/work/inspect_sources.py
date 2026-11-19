import collections,gzip,hashlib,json,sqlite3
from pathlib import Path
ROOT=Path('/scratch/jjyeung/n30_mirror/rows_a2'); OUT=Path('work')
inputs={};aliases={};conflicts=[];counts={}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 inputs[str(p)]={'sha256':h.hexdigest(),'bytes':p.stat().st_size};return h.hexdigest()
def add(p,i,raw,r,cnt):
 cnt['rows']+=1
 can=(r.get('provenance') or {}).get('canonical')
 if not can:return
 cnt['provenance_canonical_rows']+=1
 key=r['dataset']+'/'+r['scene']
 entry=dict(canonical=can,source=dict(path=str(p),sha256=inputs[str(p)]['sha256'],row_index=i,row_id=r.get('qid'),row_sha256=hashlib.sha256(raw.encode()).hexdigest(),field='provenance.canonical'),dataset=r['dataset'],scene_token=r['scene'])
 if key not in aliases:aliases[key]=entry
 elif aliases[key]['canonical']!=can:conflicts.append(dict(token=key,first=aliases[key],other=entry))
paths=sorted(ROOT.rglob('*.sqlite'))
for p in paths:
 sha(p);cnt=collections.Counter()
 with sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True) as c:
  for i,raw in c.execute('select i,row from rows order by i'):add(p,i,raw,json.loads(raw),cnt)
 counts[str(p)]=dict(cnt);print(p.relative_to(ROOT),dict(cnt),len(aliases),flush=True)
for p in [ROOT/'a2_room_ft2_v1/rows.jsonl.gz',ROOT/'a2_room_ft2_v1/slice_a2_room_ft2.jsonl']:
 sha(p);cnt=collections.Counter()
 with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:
  for i,raw in enumerate(f,1):add(p,i,raw.rstrip('\n'),json.loads(raw),cnt)
 counts[str(p)]=dict(cnt);print(p.relative_to(ROOT),dict(cnt),len(aliases),flush=True)
result=dict(inputs=inputs,aliases=aliases,conflicts=conflicts,source_counts=counts)
(OUT/'source_scan.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
Path('STATUS.md').write_text('The surviving rows_a2 SQLite stores and room inputs have been scanned for explicit provenance.canonical values. The source scan records file hashes, row witnesses, coverage inputs and conflicts in work/source_scan.json. The D0 base and token-minting builders are still being checked against the mirror archive inventory; the room audit has not run.\n')
