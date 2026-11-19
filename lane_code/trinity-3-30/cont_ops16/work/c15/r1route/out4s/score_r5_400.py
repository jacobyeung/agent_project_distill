"""Pair the R1 step-400 returns with the registered step-544 reads (cont_ops19 copy of out3s/score_r5.py: step 400, B-only allowed)."""
import argparse,copy,hashlib,json,sys,re,random
STEP=400
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
HERE=Path(__file__).resolve().parent
O=HERE.parent if HERE.name in ('A','B') else HERE
BASE=O/'bases'
CAMERA=('camera_displacement','camera_rotation','camera_movement_direction')
DISTANCE='object_abs_distance';ROOM='room_size_estimation'
sys.path[:0]=[str(O/'A'),str(O/'A/src/b'),str(O/'A/src/tree'),str(O/'A/src')]
from h1eval import scorers
from tower_pair import status

def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def bootstrap(pairs):
    groups=defaultdict(list)
    for room,value in pairs:groups[room].append(float(value))
    if not groups:return dict(value=None,ci95=None,ci9929=None,upper95=None,n=0,rooms=0)
    groups=[groups[k] for k in sorted(groups)]
    sums=np.array([sum(g) for g in groups]);counts=np.array([len(g) for g in groups])
    # Match the accepted room_bootstrap.py RNG and ratio estimator.
    rng=random.Random(17);samples=[];grouped=list(zip(sums.tolist(),counts.tolist()))
    for _ in range(10000):
        draw=rng.choices(grouped,k=len(grouped))
        samples.append(sum(v[0] for v in draw)/sum(v[1] for v in draw))
    return dict(value=float(sums.sum()/counts.sum()),ci95=np.quantile(samples,[.025,.975]).tolist(),
                ci9929=np.quantile(samples,[.00355,.99645]).tolist(),upper95=float(np.quantile(samples,.95)),n=int(counts.sum()),rooms=len(groups))

def load(root,package,read_no,step,rule):
    root=Path(root);package=Path(package);src=package/'src'
    name='room134.json' if package.name in ('b2','B') else 'devs1_routed.json'
    manifest=read(src/'items'/name);items={i['id']:i for i in manifest['items']}
    expected=copy.deepcopy(read(package/'READ_PLAN.json')['read_settings'][read_no])
    identity=read(root/'metadata/IDENTITY.json');public=read(package/'package/0.json')
    if identity['plan']!=public['plan_sha256'] or identity['operator_sha256']!=digest(package/'tower_sequence.py'):
        raise ValueError('Return plan/operator differs')
    if identity['reads'][read_no]!=expected:raise ValueError('Read plan differs')
    if step in (200,400):
        pin=read(root/'metadata/EXPORT_PIN.json');binding=read(package/'READ_PLAN.json')['export_binding']
        for k in ('run','step','member_directory','lineage','object','config_sha256'):
            if pin.get(k)!=binding[k]:raise ValueError('Export binding differs: '+k)
        for k,v in binding['preparation_sha256'].items():
            if pin['preparation'][k]['sha256']!=v:raise ValueError('Preparation differs')
    planned_types=[read(src/'9.json')['order'][i] for i in expected['types']]
    planned=[k for k,i in items.items() if i['question_type'] in planned_types]
    rows={};sources=[];shared=None
    journal_root=root/'metadata/reads'/str(read_no)/'metadata/journals'
    for started in journal_root.glob('*/*/STARTED.json'):
        if not (started.parent/'items.jsonl').is_file():raise ValueError('Started segment lacks journal')
    paths=sorted(journal_root.glob('*/*/items.jsonl'))
    if not paths:raise ValueError('No journals')
    # The reader and evaluator hashes are unchanged and are authenticated by the baseline.
    base_env=next((BASE/('b2' if package.name in ('b2','B') else 'b1')/'work/ret/metadata/reads'/str(read_no if step==544 else 0)/'metadata/journals').glob('*/*/environment.json'))
    reference=read(base_env)['binding']
    for p in paths:
        env=read(p.parent/'environment.json');b=env['binding']
        fixed=dict(arms=['tower'],modes=[{'name':'none'}],step=step,lineage='SFT',fixture=False,
                   stage1_select_rule=rule,perception_memo_modules=['g3t'],save_own_depth=False,
                   perception_memo=expected['perception_memo'],perception_memo_verify_ids=expected['perception_memo_verify_ids'],
                   items_sha256=digest(src/'items'/name),item_set_sha256=manifest['item_set_sha256'])
        for k in ('reader_sha256','parity_code_sha256','evaluator_code_sha256','maker_sha256'):fixed[k]=reference[k]
        for k,v in fixed.items():
            if b.get(k)!=v:raise ValueError('Journal binding differs: '+k)
        if b['settings_sha256']!=canonical(env['settings']):raise ValueError('Settings hash differs')
        for k in ('stage1_select_rule','perception_memo','perception_memo_modules','perception_memo_verify_ids','save_own_depth'):
            if env['settings'].get(k)!=fixed[k]:raise ValueError('Settings differ: '+k)
        current={k:b[k] for k in ('export_sha256','settings_sha256','artifact_manifest_sha256')}
        if shared is not None and current!=shared:raise ValueError('Mixed journals')
        shared=current;sources.append(dict(path=str(p),sha256=digest(p)))
        text=p.read_text()
        if text and not text.endswith('\n'):raise ValueError('Uncommitted tail')
        for line in text.splitlines():
            r=json.loads(line);k=r['id']
            if k in rows or k not in planned:raise ValueError('Duplicate or unplanned item')
            if r.get('complete') is not True or r.get('arm')!='tower' or r.get('mode')!='none':raise ValueError('Uncommitted or wrong-arm row')
            if r['type']!=items[k]['question_type'] or r['room_key']!=items[k]['room_key']:raise ValueError('Pair metadata differs')
            rows[k]=r
    return rows,items,manifest,sources

def metrics(rows,items,keys):
    available=[k for k in keys if k in rows];states=Counter();calls=Counter();finishes=Counter()
    for k in available:
        r=rows[k];rs=scorers.records(r['output']);states.update(set(status(c) for c in rs));calls.update(status(c) for c in rs);finishes.update([r['output']['finish']])
    scores={k:float(scorers.accuracy(rows[k]['output'],items[k])['task_accuracy']) for k in available}
    capped=[k for k in available if rows[k]['output'].get('finish') in ('max_calls','max_new_tokens','length')]
    with_calls=[k for k in available if scorers.records(rows[k]['output'])]
    return dict(expected=len(keys),completed=len(available),missing=sorted(set(keys)-set(available)),
      score=float(np.mean(list(scores.values()))) if scores else None,call_items=len(with_calls),call_rate=len(with_calls)/len(keys) if keys else None,
      capped=len(capped),call_capped=finishes['max_calls'],token_capped=finishes['max_new_tokens']+finishes['length'],capped_room_bootstrap=bootstrap([(items[k]['room_key'],int(k in capped)) for k in available]),
      status_items=dict(states),status_calls=dict(calls),not_seen=states['not seen'],finishes=dict(finishes)),scores

def compare(current,baseline,items,keys,baseline_read):
    a,sa=metrics(current,items,keys);b,sb=metrics(baseline,items,keys);paired=sorted(sa.keys()&sb.keys())
    delta=bootstrap([(items[k]['room_key'],100*(sa[k]-sb[k])) for k in paired])
    complete=a['completed']==b['completed']==len(keys)
    return dict(baseline_read=baseline_read,current=a,baseline=b,paired=delta,complete=complete,
                harm9929=(delta['ci9929'][1]<0) if complete and paired else None)

def unit_count(rows,items,keys):
    result={};by_unit=defaultdict(list)
    for k in keys:
        i=items[k];factor=scorers.unit_factor(i['question'])
        if factor==1:continue
        unit={100.:'cm',1/.3048:'ft',1/.0254:'in'}[factor];by_unit[unit].append(k)
        if k not in rows:continue
        out=rows[k]['output'];values=[scorers.printed(c) for c in scorers.records(out)]
        values=[v for v in values if v and v['kind']=='gap']
        # Match the accepted unit.py diagnostic: explicit answer tag, 5% tolerance,
        # and unconverted-metres precedence (including the zero-gap ambiguity).
        tags=re.findall(r'<answer>\s*(.*?)\s*</answer>',out.get('text',''),re.S)
        try:answer=float(re.match(r'\s*([-\d.]+)',tags[-1])[1])
        except (IndexError,TypeError,ValueError):answer=None
        d=values[-1]['distance'] if values else None
        near=lambda v:answer is not None and abs(answer-v)<=.05*abs(v)+1e-9
        result[k]=bool(d is not None and out.get('finish')!='max_calls' and not near(d) and near(d*factor))
    keys=[k for ks in by_unit.values() for k in ks]
    return dict(expected=len(keys),completed=len(result),correct=sum(result.values()),missing=sorted(set(keys)-set(result)),
                by_unit={u:dict(expected=len(ks),correct=sum(result.get(k,False) for k in ks)) for u,ks in by_unit.items()},
                per_item=result,definition='Accepted unit.py diagnostic: explicit numeric answer tag within 5% + 1e-9 of the last printed gap converted to the requested unit, excluding max_calls; unconverted metres take precedence, including zero gaps. Missing answer or gap counts incorrect.')

def score(a_root,b_root,self_test=False):
    ba,items,_,s0=load(BASE/'b1/work/ret',BASE/'b1',0,544,'null_argmax')
    bd,_,_,s1=load(BASE/'b1/work/ret',BASE/'b1',1,544,'candidates_argmax')
    br,room_items,manifest,s2=load(BASE/'b2/work/ret',BASE/'b2',0,544,'null_argmax')
    if self_test:
        a={**ba,**bd};b=br;s3=s4=[]
    else:
        a,_,_,s3=load(a_root,O/'A',0,STEP,'candidates_argmax') if a_root else ({},None,None,[])
        if b_root:b,_,_,s4=load(b_root,O/'B',0,STEP,'candidates_argmax')
        else:b,s4=br,[]  # A-only partial: room rows are the baseline itself and are not reported
    result=dict(self_test=self_test,bootstrap=dict(draws=10000,seed=17,unit='physical room',intervals=[.95,.9929]),difference_units='percentage points',types={},sources=s0+s1+s2+s3+s4)
    for kind in (*CAMERA,DISTANCE,ROOM):
        keys=[k for k,i in items.items() if i['question_type']==kind]
        result['types'][kind]=compare(a,bd if kind==DISTANCE else ba,items,keys,'171253/read '+('1 candidates_argmax' if kind==DISTANCE else '0 null_argmax'))
    for kind, row in result['types'].items():row['metric']='accuracy' if kind=='camera_movement_direction' else 'MRA'
    cameras=[k for k,i in items.items() if i['question_type'] in CAMERA]
    cm,_=metrics(a,items,cameras)
    result['camera_calls']=dict(expected=450,completed=cm['completed'],called=cm['call_items'],rate=cm['call_rate'],
                                below95=(cm['call_rate']<.95) if cm['completed']==450 else None,complete=cm['completed']==450)
    keys=[k for k,i in items.items() if i['question_type']==DISTANCE]
    cap_boot=bootstrap([(items[k]['room_key'],int(a[k]['output'].get('finish')=='max_calls')) for k in keys if k in a])
    result['distance_call_cap']=dict(count=sum(a[k]['output'].get('finish')=='max_calls' for k in keys if k in a),expected=150,complete=all(k in a for k in keys),room_bootstrap_rate=cap_boot,count_ci95=[150*v for v in cap_boot['ci95']] if cap_boot['ci95'] else None)
    result['distance_call_cap']['over_five']=(result['distance_call_cap']['count']>5) if result['distance_call_cap']['complete'] else None
    result['units']=dict(current=unit_count(a,items,keys),baseline=unit_count(bd,items,keys))
    ua=result['units']['current']['per_item'];ub=result['units']['baseline']['per_item']
    result['units']['paired']=bootstrap([(items[k]['room_key'],100*(int(ua[k])-int(ub[k]))) for k in sorted(ua.keys()&ub.keys())])
    if result['units']['baseline']['expected']!=107:raise ValueError('Non-metre population differs')
    result['rooms']={name:compare(b,br,room_items,ks,'172456/read 0 null_argmax') for name,ks in manifest['sets'].items()}
    saved=read(BASE/'b2/work/scores/scores.json')
    for name,value in result['rooms'].items():
        if abs(value['baseline']['score']-saved['sets'][name]['mra_answer'])>1e-12:raise ValueError('T2 mra_answer score differs')
        value['metric']='mra_answer';value['baseline_scores_sha256']=digest(BASE/'b2/work/scores/scores.json')
    all_rooms=list(room_items)
    result['room_call_rate']=bootstrap([(room_items[k]['room_key'],int(bool(scorers.records(b[k]['output'])))) for k in all_rooms if k in b])
    result['room_call_rate']['expected']=134
    result['h3_stop']=any(t['harm9929'] is True for k,t in result['types'].items() if k in CAMERA) or result['camera_calls']['below95'] is True
    result['h3_complete']=all(result['types'][k]['complete'] for k in CAMERA)
    return result

def main():
    global BASE
    p=argparse.ArgumentParser();p.add_argument('--baseline-root',type=Path,default=BASE,help='Directory containing b1 and b2 metadata, authenticated work/ret returns, and b2/work/scores/scores.json');p.add_argument('--a');p.add_argument('--b');p.add_argument('--self-test',action='store_true');p.add_argument('--out',required=True);args=p.parse_args()
    BASE=args.baseline_root.resolve()
    required=[BASE/'b1/work/ret/metadata/IDENTITY.json',BASE/'b2/work/ret/metadata/IDENTITY.json',BASE/'b2/work/scores/scores.json']
    missing=[str(p) for p in required if not p.is_file()]
    if missing:p.error('Authentic step-544 baseline files are required: '+', '.join(missing))
    if not args.self_test and not (args.a or args.b):p.error('--a or --b required')
    result=score(args.a,args.b,args.self_test);target=Path(args.out);target.mkdir(parents=True,exist_ok=True)
    (target/'scores.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=[]
    for name,r in {**result['types'],**result['rooms']}.items():
        lines.append('{}: baseline {}; {:.6f} vs {:.6f}; delta {} pp; 95% {}; 99.29% {}; complete {}'.format(name,r['baseline_read'],r['current']['score'] or 0,r['baseline']['score'] or 0,r['paired']['value'],r['paired']['ci95'],r['paired']['ci9929'],r['complete']))
    lines += ['Camera calls: '+json.dumps(result['camera_calls']),'Non-metre conversions: '+str(result['units']['current']['correct'])+'/107','Distance call caps: '+json.dumps(result['distance_call_cap']),'H3 STOP: '+str(result['h3_stop'])+'; complete: '+str(result['h3_complete'])]
    (target/'scores.txt').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))
if __name__=='__main__':main()
