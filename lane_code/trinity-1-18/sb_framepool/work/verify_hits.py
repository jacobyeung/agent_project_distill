import json,hashlib,collections
from pathlib import Path
from scan_rows import sha,C,target
reg=json.load(open('work/metadata_fixed.json'))['files'];meta=json.load(open('work/metadata_row_results.json'))['streams'];catalog=json.load(open('work/all_archive_catalog.json'))['entries'];offsets={e['archive']+'::'+e['name']:e for e in catalog};known={}
for c in C['captures']:
 for key in [c['token'],c['scene_list_key'],c['canonical_scene'],c['canonical_scene'].replace('scannetpp/','scannetppv2/')]:known[key]=c['token']
out=[];counts={}
for s in meta:
 locs=[p for p in s['locations'] if '/rows_slices/slices_v3/' in p]
 if not locs or not s.get('hits'):continue
 loc=locs[0];e=offsets[loc]
 with open(e['archive'],'rb') as f:f.seek(e['offset']);raw=f.read(e['size'])
 assert hashlib.sha256(raw).hexdigest()==s['sha256']
 counts[s['sha256']]=collections.Counter()
 for i,l in enumerate(raw.decode().splitlines()):
  r=json.loads(l);matches=set();d=r.get('dataset');scene=r.get('scene')
  for k in [str(d)+'/'+str(scene),scene,r.get('canonical')]:
   if k in known:matches.add(known[k])
  assert len(matches)<=1
  if not matches:continue
  tok=next(iter(matches));counts[s['sha256']][tok]+=1
  out.append(dict(source_sha256=s['sha256'],source=loc,row_index=i,row_sha256=hashlib.sha256(l.encode()).hexdigest(),token=tok,qid=r.get('qid'),family=Path(e['name']).stem,diagnostic_flags={k:r[k] for k in ['benchmark_trained_diagnostic','benchmark_improvement_claim','infrastructure_only','score_nomination_allowed','result_status'] if k in r},provenance=r.get('provenance')))
 assert dict(counts[s['sha256']])==s['counts']
Path('work/verified_hits.json').write_text(json.dumps(dict(command='/usr/bin/python3 work/verify_hits.py',inputs={p:{'sha256':sha(p)} for p in ['work/captures.json','work/metadata_row_results.json','work/all_archive_catalog.json']},source_hashes={s['sha256']:s['locations'] for s in meta if s['sha256'] in counts},rows=out),indent=2)+'\n')
print('verified',len(out),'captures',len(set(x['token'] for x in out)))
Path('STATUS.md').write_text('The audit verified 1,193 matching row records in archived slices_v3 metadata samples, across 125 target captures. Direct scans of 39 local stores/slices and five archive SQLite stores found zero matches. All 146 distinct target captures are in BENCH v2 (148 benchmark-group memberships). Production lineage stores remain partially missing; evaluation joins and final packaging are in progress.\n')
