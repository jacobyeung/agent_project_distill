#!/usr/bin/env python3
"""Pair the two tower reads with the step-544 own baseline using sealed scorers."""
import argparse,json,sys,hashlib,statistics
from collections import Counter
from pathlib import Path

RULES=('null_argmax','candidates_argmax')
CAMERA=('camera_displacement','camera_rotation','camera_movement_direction')
DISTANCE='object_abs_distance';ROOM='room_size_estimation'

def configure(package):
 package=Path(package).resolve()
 sys.path[:0]=[str(package/'b'),str(package/'tree'),str(package)]
 from h1eval import scorers
 from h1eval.statistics import bootstrap
 return scorers,bootstrap

def status(call):
 text=call.get('response','').strip()
 if call.get('served') is False:return 'unserved'
 if 'not seen' in text:return 'not seen'
 if text.startswith('error:'):return text.split('\n')[0]
 if ': frames ' in text:return 'selected'
 for word in ('ambiguous','unavailable','invalid','refused'):
  if word in text.lower():return word
 if not text:return 'missing response'
 return 'returned'

def load(files,items,arm,rule=None,self_check=False,expected_hashes=None):
 result={};sources=[];identity=None
 for arg in files:
  path=Path(arg)
  paths=sorted(path.rglob('items.jsonl')) if path.is_dir() else [path]
  if not paths:
   identity_path=path/'metadata/IDENTITY.json'
   if not identity_path.is_file():raise ValueError('No item journals or planned read identity: '+str(path))
   planned=json.loads(identity_path.read_text());index=RULES.index(rule)
   if planned.get('read')!=index or planned['reads'][index]['stage1_select_rule']!=rule:raise ValueError('Empty read identity differs')
   sources.append(dict(path=str(identity_path),sha256=hashlib.sha256(identity_path.read_bytes()).hexdigest(),no_completed_journals=True))
  for path in paths:
   env=path.parent/'environment.json'
   if arm=='tower' and not self_check:
    if not env.is_file():raise ValueError('Tower journal lacks its environment binding: '+str(path))
    binding=json.loads(env.read_text())['binding']
    if (binding.get('stage1_select_rule')!=rule or binding.get('arms')!=['tower']
         or binding.get('lineage')!='SFT' or binding.get('step')!=544):
     raise ValueError('Tower rule/arm/export identity differs')
    fields=('export_sha256','item_set_sha256','items_sha256','reader_sha256','maker_sha256','evaluator_code_sha256','artifact_manifest_sha256','settings_sha256','stage1_select_rule','save_own_depth','parity_code_sha256')
    current={k:binding.get(k) for k in fields}
    if identity is not None and current!=identity:raise ValueError('Partial journals have different read identities')
    identity=current
    if expected_hashes and any(binding.get(k)!=v for k,v in expected_hashes.items()):raise ValueError('Return code differs from scoring package')
   sources.append(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
   for line in path.read_text().splitlines():
    if not line.strip():continue
    row=json.loads(line)
    if row.get('mode')!='none':continue
    if row.get('arm')!=arm:raise ValueError('Unexpected arm')
    if row.get('complete') is not True:raise ValueError('Uncommitted item')
    key=row['id']
    if key not in items:raise ValueError('Unknown item key: '+key)
    item=items[key]
    if row['type']!=item['question_type'] or row['room_key']!=item['room_key']:raise ValueError('Item metadata differs')
    if rule==RULES[1] and row['type']!=DISTANCE:
     if self_check:continue
     raise ValueError('Candidates read contains an unplanned type')
    if key in result:raise ValueError('Duplicate item key: '+key)
    for c in row['output'].get('calls',{}).get('records',[]):
     d=c.get('stage1',{})
     if not self_check and rule and d.get('rule',rule)!=rule:raise ValueError('Mixed rule diagnostics')
    result[key]=row
 return result,sources

def analyse(own,towers,items,scorers,bootstrap,self_check=False):
 from b1_report import stage
 def score(row):return scorers.accuracy(row['output'],items[row['id']])['task_accuracy']
 own_scores={k:score(r) for k,r in own.items()}
 result=dict(bootstrap=dict(draws=10000,seed=20261115,unit='room',interval=.95),self_check=self_check,
             score_units='percentage points for paired differences; fractions for MRA',rules={},per_call_errors={})
 own_calls=[]
 for key,row in own.items():
  measurement=scorers.accuracy(row['output'],items[key]);numeric=iter(measurement['calls'])
  for index,c in enumerate(scorers.records(row['output'])):
   own_calls.append(dict(id=key,type=row['type'],index=index,family=c.get('family'),call=c['call'],
     status=status(c),response=c.get('response'),**{k:v for k,v in (next(numeric) if scorers.printed(c) is not None else {}).items() if k!='call'}))
 result['per_call_errors']['own']=own_calls
 for rule,tower in towers.items():
  kinds=[DISTANCE] if rule==RULES[1] else [*CAMERA,DISTANCE,ROOM]
  scores={k:score(r) for k,r in tower.items()};by_type={}
  for kind in kinds:
   expected={k for k,i in items.items() if i['question_type']==kind}
   a=set(own)&expected;b=set(tower)&expected;paired=sorted(a&b)
   delta=bootstrap([(items[k]['room_key'],100*(own_scores[k]-scores[k])) for k in paired])
   complete=bool(expected) and a==b==expected
   by_type[kind]=dict(own_n=len(a),tower_n=len(b),expected=len(expected),complete=complete,
     own_score=100*statistics.mean(own_scores[k] for k in paired) if paired else None,
     tower_score=100*statistics.mean(scores[k] for k in paired) if paired else None,
     available_own_score=100*statistics.mean(own_scores[k] for k in a) if a else None,
     available_tower_score=100*statistics.mean(scores[k] for k in b) if b else None,
     own_minus_tower=delta,missing_own=sorted(expected-a),missing_tower=sorted(expected-b),
     own_only=sorted(a-b),tower_only=sorted(b-a),
     takeover_bar_met=(delta['ci95'][0]>-5) if kind in CAMERA and complete and not self_check else None)
  table=Counter();status_reads=Counter();status_calls=Counter();errors=[];clean={};ds={};metres={};capped=0;no_ground=0
  for key,row in tower.items():
   item=items[key];measurement=scorers.accuracy(row['output'],item)
   numeric=iter(measurement['calls'])
   records=scorers.records(row['output'])
   for index,c in enumerate(records):
    errors.append(dict(id=key,type=row['type'],index=index,family=c.get('family'),call=c['call'],
                       status=status(c),response=c.get('response'),**{k:v for k,v in (next(numeric) if scorers.printed(c) is not None else {}).items() if k!='call'}))
   if row['type']!=DISTANCE:continue
   ds[key]=scores[key]
   if scorers.unit_factor(item['question'])==1:metres[key]=scores[key]
   capped+=row['output'].get('finish') in ('max_calls','max_new_tokens')
   grounds=[c for c in records if c.get('family')=='ground']
   no_ground+=not grounds
   states={status(c) for c in records};status_reads.update(states);status_calls.update(status(c) for c in records)
   if not any(status(c)!='selected' for c in grounds):clean[key]=scores[key]
   for c in grounds:table[stage(c)]+=1
  n=len(ds)
  result['rules'][rule]=dict(by_type=by_type,distance=dict(reads=n,task_mra=statistics.mean(ds.values()) if n else None,
    metre_items=len(metres),metre_mra=statistics.mean(metres.values()) if metres else None,
    no_failed_ground_items=len(clean),no_failed_ground_mra=statistics.mean(clean.values()) if clean else None,
    no_ground_calls=no_ground,no_failed_ground_definition='No ground call has a status other than selected; includes reads with no ground calls.',
    capped_reads=capped,capped_share=capped/n if n else None,status_reads=dict(status_reads),
    status_shares={k:v/n for k,v in status_reads.items()} if n else {},status_calls=dict(status_calls),
    stage_table=dict(table)))
  result['per_call_errors'][rule]=errors
 result['any_camera_meets_takeover_bar']=any(v['takeover_bar_met'] is True for v in result['rules'][RULES[0]]['by_type'].values()) if not self_check else None
 return result

def markdown(result):
 lines=['# Step-544 own and tower pairing','',
  'Differences are own minus tower in percentage points. Intervals resample paired rooms 10,000 times with seed 20261115.',
  'Missing items remain missing; incomplete types cannot establish the take-over bar.','',
  '| Rule | Type | Paired / expected | Paired own | Paired tower | Difference [95% interval] | Bar met |',
  '|---|---|---:|---:|---:|---|---|']
 def fmt(x):return 'n/a' if x is None else f'{x:.4f}'
 for rule,r in result['rules'].items():
  for kind,t in r['by_type'].items():
   d=t['own_minus_tower'];ci=d['ci95']
   lines.append(f"| {rule} | {kind} | {d['n']} / {t['expected']} | {fmt(t['own_score'])} | {fmt(t['tower_score'])} | {fmt(d['value'])} [{', '.join(map(fmt,ci)) if ci else 'n/a'}] | {t['takeover_bar_met']} |")
  d=r['distance'];lines+=['',f'## Distance: {rule}','',
   f"{d['reads']} reads; {d['capped_reads']} capped ({fmt(d['capped_share'])}). MRA: {fmt(d['task_mra'])} on all units, {fmt(d['metre_mra'])} on {d['metre_items']} metre questions, and {fmt(d['no_failed_ground_mra'])} on {d['no_failed_ground_items']} reads without a failed ground.",
   d['no_failed_ground_definition'],'','| Status in any call | Reads | Share |','|---|---:|---:|']
  for k,n in sorted(d['status_reads'].items()):lines.append(f"| {k} | {n} | {fmt(d['status_shares'][k])} |")
  lines+=['','Status shares can overlap within a read. Capped calls remain unserved.','','| Ground diagnostic stage | Calls |','|---|---:|']
  for k,n in sorted(d['stage_table'].items()):lines.append(f'| {k} | {n} |')
 lines+=['','## Missing keys','']
 for rule,r in result['rules'].items():
  for kind,t in r['by_type'].items():
   lines.append(f"{rule}, {kind}: missing own {json.dumps(t['missing_own'])}; missing tower {json.dumps(t['missing_tower'])}.")
 lines+=['','## Per-call errors','',
  'The following errors use the package scorer. Every call, including unserved and nonnumeric responses, is retained in `curve.json` under `per_call_errors`.','',
  '| Rule | Item | Call index | Status | Metre error | Degree error | Direction correct |',
  '|---|---|---:|---|---:|---:|---|']
 for rule,rows in result['per_call_errors'].items():
  for r in rows:
   lines.append(f"| {rule} | {r['id']} | {r['index']} | {r['status']} | {fmt(r.get('absolute_error_m'))} | {fmt(r.get('error_deg'))} | {r.get('correct','n/a')} |")
 lines+=['',f"Any camera type meets the bar: {result['any_camera_meets_takeover_bar']}."]
 if result['self_check']:lines+=['','This is an own-versus-own self-check; it is not evidence about the tower arm.']
 return '\n'.join(lines)+'\n'

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True);p.add_argument('--items')
 p.add_argument('--own',nargs='+',required=True);p.add_argument('--tower-null',nargs='+',required=True)
 p.add_argument('--tower-candidates',nargs='+',required=True);p.add_argument('--out',required=True);p.add_argument('--self-check',action='store_true')
 a=p.parse_args();scorers,bootstrap=configure(a.package)
 items={i['id']:i for i in json.loads(Path(a.items or Path(a.package)/'items/devs1_routed.json').read_text())['items']}
 own,osrc=load(a.own,items,'own');towers={};sources={'own':osrc}
 from h1eval.cli import code_hash
 expected_hashes=dict(evaluator_code_sha256=code_hash(),reader_sha256=code_hash(Path(a.package)/'b/e2e_reader'))
 for rule,files in zip(RULES,(a.tower_null,a.tower_candidates)):
  towers[rule],sources[rule]=load(files,items,'own' if a.self_check else 'tower',rule,a.self_check,expected_hashes)
 result=analyse(own,towers,items,scorers,bootstrap,a.self_check);result['sources']=sources
 from h1eval.cli import code_hash
 result['evaluator_code_sha256']=code_hash();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 (out/'curve.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 (out/'TOWER_ARM_DEVS1.md').write_text(markdown(result))
 if a.self_check:
  for r in result['rules'].values():
   for t in r['by_type'].values():
    assert t['complete'] and t['own_minus_tower']['value']==0 and t['own_minus_tower']['ci95']==[0,0]
 print(json.dumps(dict(out=str(out),self_check=a.self_check,complete={r:all(t['complete'] for t in v['by_type'].values()) for r,v in result['rules'].items()})))

if __name__=='__main__':main()
