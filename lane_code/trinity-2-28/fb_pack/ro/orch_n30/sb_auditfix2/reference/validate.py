"""Validate proof replay, accounting, and every exported hit example."""
import ast,collections,hashlib,json,re,sqlite3
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent;inputs={}
def read(p):
 b=Path(p).read_bytes();inputs[str(p)]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return json.loads(b)
a=read(BASE/'out/ROOM_AUDIT_TIERED.json');m=read(BASE/'out/TIERED_ALIAS_MAP.json');c=read(BASE/'out/TIER_CHECKS.json')
assert a['rows']==a['resolved_rows']+a['unresolved_rows']==204413
assert a['baseline']['resolved']==85038 and a['baseline']['K1']==2637 and a['baseline']['R0']==0
assert sum(v['rows'] for v in a['room_resolved_coverage'].values())==a['resolved_rows']
assert sum(a['unresolved_tokens'].values())==a['unresolved_rows']
assert sum(a['unresolved_by_stream'].values())==sum(a['unresolved_by_family'].values())==a['unresolved_rows']
assert all(x['disagreements']==0 for x in c['function_checks'].values())
checks=collections.Counter()
for key,e in m['aliases'].items():
 if 'C' in e['supporting_tiers']:
  p=e['preimage_proof'];h=hashlib.sha256(p['preimage'].encode()).hexdigest();assert h==p['sha256'];assert key.split('/',1)[1]=='v'+h[:12];assert key==p['printed_token'];checks['preimages_replayed']+=1
 if 'A' in e['supporting_tiers']:assert e['source_row_witness']['sha256'] in [v['sha256'] for v in m['inputs'].values()];checks['witness_bindings']+=1
 if 'B' in e['supporting_tiers']:assert e['archived_map_proof']['sha256'].startswith('488480ab');checks['archive_bindings']+=1
for n,total in a['hits'].items():
 assert total==sum(a['hits_by_tier'][n].values())==sum(a['hits_by_stream'][n].values())==sum(a['hits_by_family'][n].values())
 joint=[r for r in a['hits_by_list_tier_stream_family'] if r['list']==n];assert sum(r['rows'] for r in joint)==total
 for t,count in a['hits_by_tier'][n].items():
  assert sum(r['rows'] for r in joint if r['tier']==t)==count
  assert len(a['examples_by_list_tier'][n][t])==min(count,20)
 checks['list_accounting']+=1
# Check exported examples against immutable store rows and selected token proof.
db=Path(a['store']['path']);assert a['inputs'][str(db)]['sha256']==a['store']['sha256']
with sqlite3.connect(db.as_uri()+'?mode=ro&immutable=1',uri=True) as conn:
 for n,tiers in a['examples_by_list_tier'].items():
  for t,examples in tiers.items():
   for e in examples:
    raw=conn.execute('select row from rows where i=?',(e['row_index'],)).fetchone()[0];r=json.loads(raw)
    assert r['qid']==e['row_id'] and r['dataset']==e['dataset'] and r['scene']==e['scene_token'];assert r.get('pool','MISSING')==e['stream'] and r.get('question_type','MISSING')==e['family']
    assert m['aliases'][e['token']]['canonical']==e['canonical'] and m['aliases'][e['token']]['tier']==t
    checks['example_rows_verified']+=1
assert len((BASE/'out/ROOM_AUDIT_REPORT.md').read_text().splitlines())<=80
p=Path(__file__).resolve();inputs[str(p)]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(BASE/'work/VALIDATION.json').write_text(json.dumps(dict(command='python work/validate.py',inputs=inputs,status='PASS',checks=dict(checks)),indent=2)+'\n');print(dict(checks))
