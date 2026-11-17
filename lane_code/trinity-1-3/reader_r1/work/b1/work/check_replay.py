from pathlib import Path
import json,re,statistics,collections
W=Path(__file__).resolve().parents[1]
def rows(path):return [json.loads(l) for l in path.read_text().splitlines()]
def key(r):return r['id'],r['geo'],r['rule']
expected={key(r):r for r in rows(W/'in/replay/replay_out2.jsonl')}
actual={key(r):r for r in rows(W/'out/replay_patched.jsonl')}
assert set(actual)==set(expected),(len(actual),len(expected))
mismatches=[];errors=[];max_diag=0
for k,e in expected.items():
 a=actual[k]
 if 'error' in e or 'error' in a:
  errors.append(dict(key=k,expected=e.get('error'),actual=a.get('error')))
  if e.get('error')!=a.get('error'):mismatches.append(dict(key=k,kind='error',expected=e.get('error'),actual=a.get('error')))
  continue
 for field in ('ground','gap','queries'):
  if a[field]!=e[field]:mismatches.append(dict(key=k,field=field,expected=e[field],actual=a[field]))
 for name,d in a['stage1'].items():
  max_diag=max(max_diag,len(json.dumps(d,allow_nan=False).encode()))
  assert len(d['sam3']['kept_per_frame'])==32
  assert len(d['candidates'])<=30
  assert all(len(c['inputs'])==58 for c in d['candidates'])
  assert d['rule']==a['rule']
items={i['id']:i for i in json.loads((W/'work/p/items/devs1_routed.json').read_text())['items']}
pairs=json.loads((W/'in/replay/pairs_cache.json').read_text())
known={(p['id'],p['name']):p for p in pairs}
import sys
sys.path.insert(0,str(W/'out'));from b1_report import unit_factor,mra
report=dict(runs=len(actual),expected_errors=errors,mismatches=mismatches,max_diagnostic_bytes=max_diag,table=[])
for geo in ('tower','hybrid'):
 sets={rule:[r for r in actual.values() if r['geo']==geo and r['rule']==rule and 'error' not in r] for rule in ('null_argmax','candidates_argmax')}
 for rule,values in sets.items():
  pair_keys={(r['id'],n) for r in values for n in r['ground'] if (r['id'],n) in known}
  ns=[(r['id'],n) for r in values for n,s in r['ground'].items() if s.strip().endswith(': not seen')]
  table=dict(geometry=geo,rule=rule,reads=len(values),pairs=len(pair_keys),not_seen_pairs=len(ns),
     not_seen_reads=sum(any(s.strip().endswith(': not seen') for s in r['ground'].values()) for r in values),
     empty_candidate_pairs=sum(d['linked_candidates']==0 for r in values for d in r['stage1'].values()),
     expected_not_seen_pairs={('tower','null_argmax'):54,('hybrid','null_argmax'):70,('tower','candidates_argmax'):7,('hybrid','candidates_argmax'):7}[(geo,rule)])
  if rule=='candidates_argmax':
   table['remaining_classes']=dict(collections.Counter(known[k]['cls'] for k in ns))
   assert len(ns)==7,table
  report['table'].append(table)
 baseline={r['id']:r for r in sets['null_argmax']};cl=[];resc=[]
 def value(r):
  match=re.fullmatch(r'distance ([\d.]+) m',r['gap'] or '')
  return float(match[1]) if match else None
 for r in sets['candidates_argmax']:
  base=baseline[r['id']];clean=not any(s.strip().endswith(': not seen') for s in base['ground'].values())
  v=value(base if clean else r)
  if v is None:continue
  item=items[r['id']];gt=float(item['ground_truth'])/unit_factor(item['question'])
  (cl if clean else resc).append(mra(v,gt))
 report[geo+'_accuracy']=dict(clean_n=len(cl),rescued_n=len(resc),clean_mra=statistics.mean(cl),rescued_mra=statistics.mean(resc),
       record_clean_mra=.500 if geo=='hybrid' else .646,record_rescued_mra=.496 if geo=='hybrid' else .534)
assert max_diag<64*1024,max_diag
(W/'out/REPLAY_CHECK.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
assert not mismatches,mismatches[:3]
