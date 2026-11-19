"""Score the tower-and-own camera read: own, tower and own minus tower per camera type.

Differences are percentage points, paired by item, with score_r5.bootstrap
(physical-room resampling, random.Random(17), 10,000 draws). The registered
step-544 intervals came from h1eval.statistics.bootstrap (seed 20261115), which
is printed beside them as "544-RNG" so that comparison is like for like.
Any refusal, including a paired set short of 450 own and 450 tower rows, exits 2 with
a one-line reason and writes nothing; --allow-partial scores an incomplete set as a
diagnostic that marks every line PARTIAL and withholds the decision.
"""
import argparse,hashlib,json,sys
from pathlib import Path

KIT=Path(__file__).resolve().parent
CAMERA=('camera_displacement','camera_movement_direction','camera_rotation')
VENDOR={'score_r5.py':'476315803c3c995e5f4cba2395505ec560148db3af16fb36bd7761c739ac3ed7',
        'tower_pair.py':'ea0ae8eb4a54821323a38c9f2701219b58ec4c29f8e84d93456e40f8851ce9ad'}
# Registered step-544 camera figures: own from job 170631, tower from job 171253 read 0 (null_argmax).
REGISTERED_544={
 'camera_displacement':dict(own=47.2,tower=82.3,own_minus_tower=-35.13,ci95=[-43.16,-27.39]),
 'camera_movement_direction':dict(own=75.3,tower=94.7,own_minus_tower=-19.33,ci95=[-27.48,-11.89]),
 'camera_rotation':dict(own=42.7,tower=75.6,own_minus_tower=-32.87,ci95=[-39.44,-26.42])}
BAR=-5.0

def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def scoring(package):
 for name,h in VENDOR.items():
  if digest(KIT/'vendor'/name)!=h:raise ValueError('Vendored scorer differs: '+name)
 src=Path(package)/'src'
 sys.path[:0]=[str(KIT/'vendor'),str(src/'b'),str(src/'tree'),str(src)]
 import score_r5
 from h1eval import scorers
 from h1eval.statistics import bootstrap as registered_bootstrap
 return score_r5,scorers,registered_bootstrap

def references():
 refs=read(KIT/'ref/REFS.json');rows={}
 for name,r in refs.items():
  raw=(KIT/'ref'/f'{name}.jsonl').read_bytes()
  if hashlib.sha256(raw).hexdigest()!=r['sha256']:raise ValueError('Reference rows differ: '+name)
  rows[name]={};
  for line in raw.decode().splitlines():
   v=json.loads(line)
   if v['id'] in rows[name]:raise ValueError('Duplicate reference row')
   rows[name][v['id']]=v
 return refs,rows

def load(root,package,refs,fixture=False,allow_partial=False):
 """Authenticate a fork return against its package and A4's tower settings, then index rows by arm.

 Each journal must declare exactly its planned type-and-card members as binding ids and hold rows only for
 them. Unless allow_partial, every planned item must have a row in both arms.
 """
 root=Path(root);package=Path(package);src=package/'src'
 manifest=read(src/'items/devs1_routed.json');items={i['id']:i for i in manifest['items']}
 plan=read(package/'READ_PLAN.json');expected=plan['read_settings'][0];public=read(package/'package/0.json')
 identity=read(root/'metadata/IDENTITY.json')
 if identity['plan']!=public['plan_sha256'] or identity['operator_sha256']!=digest(package/'tower_sequence.py'):
  raise ValueError('Return plan/operator differs')
 if identity['reads'][0]!=expected or identity['cards']!=1:raise ValueError('Read plan differs')
 binding=plan['export_binding']
 pin=read(root/'metadata/EXPORT_PIN.json')
 for k in ('run','step','member_directory','lineage','object','config_sha256','archive_sha256'):
  if pin.get(k)!=binding[k]:raise ValueError('Export binding differs: '+k)
 for k,v in binding['preparation_sha256'].items():
  if pin['preparation'][k]['sha256']!=v:raise ValueError('Preparation differs: '+k)
 inputs=read(root/'metadata/INPUTS.json')
 if identity['inputs']!=canonical({k:v for k,v in inputs.items() if k!='resume'}):raise ValueError('Return inputs differ from its identity')
 if inputs['archives'][0]['sha256']!=binding['archive_sha256']:raise ValueError('Input export archive differs from the plan')
 order=read(src/'9.json')['order'];planned_types={order[t] for t in expected['types']}
 planned={k for k,i in items.items() if i['question_type'] in planned_types}
 a4=refs['tower200']
 fixed=dict(arms=list(expected['arms']),modes=[{'name':'none'}],step=binding['step'],lineage=binding['lineage'],fixture=fixture,
            items_sha256=digest(src/'items/devs1_routed.json'),item_set_sha256=manifest['item_set_sha256'],count=manifest['count'])
 # A fixture read uses the replay maker, which loads no settings and no reader code.
 if not fixture:
  fixed.update({k:expected[k] for k in ('stage1_select_rule','save_own_depth','perception_memo','perception_memo_modules','perception_memo_verify_ids')})
  for k in ('reader_sha256','parity_code_sha256','evaluator_code_sha256','maker_sha256','settings_sha256'):fixed[k]=a4['binding'][k]
 rows={a:{} for a in expected['arms']};sources=[];shared=None
 journals=root/'metadata/reads/0/metadata/journals'
 paths=sorted(journals.glob('*/*/items.jsonl'))
 if not paths:raise ValueError('No journals')
 for p in paths:
  env=read(p.parent/'environment.json');b=env['binding']
  for k,v in fixed.items():
   if b.get(k)!=v:raise ValueError('Journal binding differs: '+k)
  if not fixture and b['settings_sha256']!=canonical(env['settings']):raise ValueError('Settings hash differs')
  current={k:b.get(k) for k in ('export_sha256','settings_sha256','artifact_manifest_sha256')}
  if shared is not None and current!=shared:raise ValueError('Mixed journals')
  shared=current;sources.append(dict(path=str(p),sha256=digest(p)))
  name=str(p.parent.relative_to(journals));t,card=p.parent.parent.name,p.parent.name
  if not (t.isdigit() and int(t)<len(order) and order[int(t)] in planned_types and card.isdigit() and int(card)<identity['cards']):
   raise ValueError('Unplanned journal: '+name)
  if b.get('shard')!=f"{card}/{identity['cards']}":raise ValueError('Journal shard differs from its directory: '+name)
  members=[i['id'] for i in manifest['items'][int(card)::identity['cards']] if i['question_type']==order[int(t)]]
  if b.get('ids')!=members:raise ValueError('Journal ids differ from its planned members: '+name)
  declared=set(members)
  text=p.read_text()
  if text and not text.endswith('\n'):raise ValueError('Uncommitted tail')
  for line in text.splitlines():
   r=json.loads(line);k=r['id'];arm=r.get('arm')
   if arm not in rows or k not in planned or k in rows[arm]:raise ValueError('Duplicate, unplanned or wrong-arm row')
   if k not in declared:raise ValueError('Row outside its journal ids: '+name)
   if r.get('complete') is not True or r.get('mode')!='none':raise ValueError('Uncommitted or wrong-mode row')
   if r['type']!=items[k]['question_type'] or r['room_key']!=items[k]['room_key']:raise ValueError('Pair metadata differs')
   rows[arm][k]=r
 gaps=[]
 for kind in sorted(planned_types):
  keys=[k for k in planned if items[k]['question_type']==kind]
  if any(k not in rows[a] for a in rows for k in keys):
   gaps.append(kind+' '+', '.join(f'{a} {sum(k in rows[a] for k in keys)}/{len(keys)}' for a in rows))
 if gaps and not allow_partial:raise ValueError('Incomplete paired set ('+'; '.join(gaps)+'); --allow-partial scores it as a diagnostic only')
 return rows,items,sources,dict(step=binding['step'],token=public['token'],plan=public['plan_sha256'],shared=shared)

def score(root,package,fixture=False,allow_partial=False):
 score_r5,scorers,registered_bootstrap=scoring(package)
 refs,ref=references()
 rows,items,sources,info=load(root,package,refs,fixture,allow_partial)
 def scores(table):return {k:float(scorers.accuracy(r['output'],items[k])['task_accuracy']) for k,r in table.items()}
 own,tower=scores(rows['own']),scores(rows['tower'])
 base={name:scores(table) for name,table in ref.items()}
 def paired(a,b,keys):
  common=[k for k in keys if k in a and k in b]
  pairs=[(items[k]['room_key'],100*(a[k]-b[k])) for k in common]
  d=score_r5.bootstrap(pairs);d['ci95_544rng']=registered_bootstrap(pairs)['ci95'];d['paired_items']=len(common)
  return d
 result=dict(return_root=str(Path(root).resolve()),package=str(Path(package).resolve()),fixture=fixture,partial=allow_partial,**info,
             bootstrap=dict(primary='score_r5.bootstrap: physical room, random.Random(17), 10000 draws, ratio estimator',
                            ci95_544rng='h1eval.statistics.bootstrap: numpy default_rng(20261115), 10000 draws'),
             units='percentage points',bar=dict(points=BAR,point='own minus tower >= -5',interval='95% lower bound > -5'),
             sources=sources,references={k:dict(job=v['job'],step=v['step'],arm=v['arm'],rule=v['rule'],sha256=v['sha256']) for k,v in refs.items()},types={})
 for kind in CAMERA:
  keys=[k for k,i in items.items() if i['question_type']==kind]
  gap=paired(own,tower,keys);complete=all(k in own and k in tower for k in keys)
  mean=lambda s,ks:100*sum(s[k] for k in ks)/len(ks) if ks else None
  common=[k for k in keys if k in own and k in tower]
  reg=dict(REGISTERED_544[kind],own=mean(base['own544'],keys),tower=mean(base['tower544'],keys))
  registered=paired(base['own544'],base['tower544'],keys)
  if (round(reg['own'],1),round(reg['tower'],1),round(registered['value'],2),[round(x,2) for x in registered['ci95_544rng']])!=(
      REGISTERED_544[kind]['own'],REGISTERED_544[kind]['tower'],reg['own_minus_tower'],reg['ci95']):
   raise ValueError('Reference rows no longer reproduce the registered step-544 figures: '+kind)
  t=dict(expected=len(keys),own_n=sum(k in own for k in keys),tower_n=sum(k in tower for k in keys),complete=complete,
         metric='accuracy' if kind=='camera_movement_direction' else 'MRA',
         own=mean(own,common),tower=mean(tower,common),own_minus_tower=gap,
         within_bar_point=(gap['value']>=BAR) if complete else None,
         within_bar_interval=(gap['ci95'][0]>BAR) if complete else None,
         vs_544_unpaired_reference=dict(registered=reg,own_change=mean(own,common)-reg['own'] if common else None,
           tower_change=mean(tower,common)-reg['tower'] if common else None,
           gap_change=gap['value']-reg['own_minus_tower'] if common else None),
         vs_544_rows=dict(own_minus_own544=paired(own,base['own544'],keys),tower_minus_tower544=paired(tower,base['tower544'],keys),
           gap_544=registered),
         vs_200_tower=dict(tower_minus_tower200=paired(tower,base['tower200'],keys),own_minus_tower200=paired(own,base['tower200'],keys)))
  result['types'][kind]=t
 done=[t for t in result['types'].values() if t['complete']]
 result['all_complete']=len(done)==len(CAMERA)
 decide=result['all_complete'] and not allow_partial
 result['all_within_bar_point']=all(t['within_bar_point'] for t in done) if decide else None
 result['all_within_bar_interval']=all(t['within_bar_interval'] for t in done) if decide else None
 return result

def find_package(root):
 """unpack_return.py writes inside its build's parent, so search that level only."""
 plan=read(Path(root)/'metadata/IDENTITY.json')['plan']
 for parent in list(Path(root).resolve().parents)[:3]:
  found=[d for d in parent.iterdir() if (d/'package/0.json').is_file() and (d/'tower_sequence.py').is_file()
         and read(d/'package/0.json')['plan_sha256']==plan]
  if len(found)>1:raise ValueError('Several builds share the return plan; pass --package')
  if found:return found[0]
 raise ValueError('No build with the return plan beside the return; pass --package')

def fmt(d):return 'n/a' if d['value'] is None else '{:+.2f} [{:+.2f}, {:+.2f}]'.format(d['value'],*d['ci95'])

def text(r):
 lines=[f"ownread {'FIXTURE (not a measurement) ' if r['fixture'] else ''}| return {r['return_root']} | token {r['token']} | export step {r['step']}",
        'Paired by item; [..] = 95% room bootstrap (score_r5.bootstrap); 544-RNG = the RNG of the registered step-544 intervals; points are pp.','',
        'type | own | tower | own-tower [95%] | 99.29% | 544-RNG 95% | n own/tower | within 5: point / 95% lower']
 for kind,t in r['types'].items():
  g=t['own_minus_tower']
  lines.append('{} | {} | {} | {} | {} | {} | {}/{} of {} | {} / {}'.format(kind,
   'n/a' if t['own'] is None else '%.2f'%t['own'],'n/a' if t['tower'] is None else '%.2f'%t['tower'],fmt(g),
   'n/a' if g['ci9929'] is None else '[{:+.2f}, {:+.2f}]'.format(*g['ci9929']),
   'n/a' if g['ci95_544rng'] is None else '[{:+.2f}, {:+.2f}]'.format(*g['ci95_544rng']),
   t['own_n'],t['tower_n'],t['expected'],t['within_bar_point'],t['within_bar_interval']))
 lines+=['','vs step 544 (unpaired reference: registered means, own 170631, tower 171253 read 0 null_argmax)',
         'type | own - own544 | tower - tower544 | gap - gap544 | registered gap [544-RNG 95%]']
 for kind,t in r['types'].items():
  v=t['vs_544_unpaired_reference'];reg=v['registered']
  f=lambda x:'n/a' if x is None else '%+.2f'%x
  lines.append(f"{kind} | {f(v['own_change'])} | {f(v['tower_change'])} | {f(v['gap_change'])} | {reg['own_minus_tower']:+.2f} [{reg['ci95'][0]:+.2f}, {reg['ci95'][1]:+.2f}]")
 lines+=['','vs step 544 rows (paired by item; same 450 items)','type | own - own544 | tower - tower544 | 544 gap recomputed']
 for kind,t in r['types'].items():
  v=t['vs_544_rows'];lines.append(f"{kind} | {fmt(v['own_minus_own544'])} | {fmt(v['tower_minus_tower544'])} | {fmt(v['gap_544'])}")
 lines+=['','vs step-200 tower return (A4, job 172744, candidates_argmax; paired by item)','type | tower - tower200 | own - tower200']
 for kind,t in r['types'].items():
  v=t['vs_200_tower'];lines.append(f"{kind} | {fmt(v['tower_minus_tower200'])} | {fmt(v['own_minus_tower200'])}")
 lines+=['',f"All three complete: {r['all_complete']}; own within 5 pp of tower on all three: point {r['all_within_bar_point']}, 95% lower bound {r['all_within_bar_interval']}"]
 if r['partial']:
  lines+=['--allow-partial: diagnostic only, no decision; score a complete return without it']
  lines=['PARTIAL | '+l if l else 'PARTIAL' for l in lines]
 return '\n'.join(lines)+'\n'

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',required=True,help='unpacked return (unpack_return.py --out)')
 p.add_argument('--out',required=True,type=Path)
 p.add_argument('--package',type=Path,help='build directory whose 1.tgz the job ran; default: the sibling build whose plan the return names')
 p.add_argument('--fixture',action='store_true',help='accept a CPU fixture return (fixture binding, replay maker)')
 p.add_argument('--allow-partial',action='store_true',help='diagnostic only: score an incomplete paired set, mark every line PARTIAL, withhold the decision')
 a=p.parse_args(argv)
 try:result=score(a.root,a.package or find_package(a.root),a.fixture,a.allow_partial)
 except (ValueError,OSError,KeyError) as e:
  p.exit(2,'ownread refused: '+' '.join((str(e) if isinstance(e,ValueError) else f'{type(e).__name__} {e}').split())+'\n')
 a.out.mkdir(parents=True,exist_ok=True)
 (a.out/'ownread.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 body=text(result);(a.out/'ownread.txt').write_text(body);print(body,end='')
 return result

if __name__=='__main__':main()
