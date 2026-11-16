"""Registered boundary decisions from complete, authenticated merged results."""
import argparse
from collections import Counter,defaultdict
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def index(rs):
    out={r['key']:r for r in rs}
    if len(out)!=len(rs): raise ValueError('Duplicate item')
    for r in rs:
        if not r.get('room'): raise ValueError('Physical room missing')
        for s in r['scores'].values():
            if s is not None and (not isinstance(s,(int,float)) or not math.isfinite(s) or not 0<=s<=1):
                raise ValueError('Invalid score')
    return out

def paired(a,b,field='released_answer',draws=10000):
    import numpy as np
    aa,bb=index(a),index(b)
    if aa.keys()!=bb.keys(): raise ValueError('Paired membership differs')
    groups=defaultdict(list)
    for k,x in aa.items():
        y=bb[k]
        if any(x[f]!=y[f] for f in ('room','question_type','stratum')): raise ValueError('Paired metadata differs')
        v,w=x['scores'][field],y['scores'][field]
        if v is None or w is None: raise ValueError('Required comparison label missing')
        groups[x['room']].append(v-w)
    if not groups: return dict(items=0,rooms=0,delta_pp=None,ci95_pp=None)
    g=np.array([(sum(v),len(v)) for k,v in sorted(groups.items())],dtype=float)
    rng=np.random.default_rng(17); samples=[]
    for first in range(0,draws,250):
        picked=g[rng.integers(0,len(g),size=(min(250,draws-first),len(g)))]
        samples.extend((100*picked[:,:,0].sum(1)/picked[:,:,1].sum(1)).tolist())
    return dict(items=len(a),rooms=len(g),delta_pp=100*float(g[:,0].sum()/g[:,1].sum()),
                ci95_pp=np.quantile(samples,[.025,.975]).tolist(),draws=draws,seed=17,
                estimator='item-weighted mean; resample whole physical rooms')

def comparison(a,b,field):
    return dict(overall=paired(a,b,field),per_type={t:paired([r for r in a if r['question_type']==t],
        [r for r in b if r['question_type']==t],field) for t in sorted({r['question_type'] for r in a})})

def aggregate(rs,field):
    if any(r['scores'][field] is None for r in rs): raise ValueError('Missing required labels')
    n=len(rs)
    return dict(items=n,score_pct=100*sum(r['scores'][field] for r in rs)/n if n else None,
                capped=sum(r['capped'] for r in rs),caps_per_100=100*sum(r['capped'] for r in rs)/n if n else None,
                unanswered=sum(r.get('unanswered',False) for r in rs),unparsed=sum(r.get('unparsed',False) for r in rs))

def load_merge(path,arm='B2048',expected_model=None):
    p=local(path); complete=load(p/'MERGE_COMPLETE.json'); receipt=load(p/'MERGE_INPUTS.json')
    if receipt.get('synthetic'):raise ValueError('Synthetic merges cannot enter empirical decisions')
    if sha(p/'MERGE_INPUTS.json')!=complete['receipt_sha256']: raise ValueError('Merge receipt hash differs')
    export=p/'report'/complete['exports'][arm]
    if sha(export)!=complete['export_sha256'][arm]: raise ValueError('Merged export hash differs')
    value=load(export); index(value['rows'])
    if value['arm']!=arm: raise ValueError('Wrong budget arm')
    cfg=load(p/'request.json')
    expected=hashlib.sha256(json.dumps({k:v for k,v in cfg.items() if k not in ('binding','output')},sort_keys=True).encode()).hexdigest()
    if cfg['binding']!=expected or value['request_binding']!=expected or receipt['request_binding']!=expected:
        raise ValueError('Request binding differs')
    if expected_model is not None and value['model']!=expected_model: raise ValueError('Wrong comparator model')
    if cfg['build_only']: raise ValueError('Dry bind is not empirical evidence')
    for name,h in receipt['inputs'].items():
        if Path(name).name!=name or sha(p/'results/0'/name)!=h: raise ValueError('Journal/receipt hash differs')
    # Verify exact fixed payload membership and physical rooms, not just row count.
    taskfile=checked(cfg['datasets'][0]['rows']); tasks=rows(taskfile)
    lookup={'devrows:'+t['id']:t for t in tasks}
    if set(lookup)!=set(index(value['rows'])): raise ValueError('Merged membership differs from fixed tasks')
    if value['strata_sha256']!=cfg['devs1']['pins']['STRATA.jsonl']: raise ValueError('Strata hash differs')
    for r in value['rows']:
        t=lookup[r['key']]
        if any(r[k]!=t[k] for k in ('room','question_type','stratum')): raise ValueError('Task metadata differs')
    # Source journals are authenticated by MERGE_INPUTS, unlike an editable summary.
    filename='g0.jsonl' if arm=='ON16k' else 'budget_'+arm[1:]+'.g0.jsonl'
    journal={}
    for r in rows(p/'results/0'/filename):
        if r.get('status')!='complete': continue
        k=r['key']
        if k in journal and journal[k]!=r: raise ValueError('Conflicting complete records')
        journal[k]=r
    if set(journal)!=set(lookup): raise ValueError('Incomplete source journal')
    for r in value['rows']:
        jr=journal[r['key']]; t=lookup[r['key']]
        r['prediction']=jr.get('extracted_answer',jr.get('response_text',''))
        r['options']=t['options']; r['answer']=t['answer']
    value['artifact']=cfg['models'][cfg['cells'][0]['model']]
    value['merge_path']=str(p)
    return value

def below_zero(comp):
    return [t for t,r in comp['per_type'].items() if r['ci95_pp'] is not None and r['ci95_pp'][1]<0]

def official_ledger(a,b,require_full=True):
    """VSI's eight-task macro, with direction the mean of its three subtypes."""
    import numpy as np
    types=['object_counting','object_abs_distance','object_size_estimation','room_size_estimation',
           'object_rel_distance','obj_appearance_order','route_planning',
           'object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard']
    aa,bb=index(a),index(b)
    if aa.keys()!=bb.keys() or (require_full and len(aa)!=5130):raise ValueError('Official ledger requires paired full 5130 membership')
    if {r['question_type'] for r in a}!=set(types):raise ValueError('Official eight-task macro types differ')
    rooms=sorted({r['room'] for r in a});ri={r:i for i,r in enumerate(rooms)}
    sums=np.zeros((len(rooms),10));counts=np.zeros_like(sums)
    for k,x in aa.items():
        y=bb[k]
        if any(x[f]!=y[f] for f in ('room','question_type')):raise ValueError('Official paired metadata differs')
        v,w=x['scores']['released_answer'],y['scores']['released_answer']
        if v is None or w is None:raise ValueError('Official labels missing')
        i,j=ri[x['room']],types.index(x['question_type']);sums[i,j]+=v-w;counts[i,j]+=1
    def macro(s,c):
        if np.any(c==0):raise ValueError('A room bootstrap draw lacks an official type; interval is not estimable')
        v=s/c;return 100*(v[...,:7].sum(-1)+v[...,7:].mean(-1))/8
    delta=float(macro(sums.sum(0),counts.sum(0)));samples=[];rng=np.random.default_rng(17)
    for _ in range(40):
        ix=rng.integers(0,len(rooms),size=(250,len(rooms)))
        samples.extend(macro(sums[ix].sum(1),counts[ix].sum(1)).tolist())
    ci=np.quantile(samples,[.025,.975]).tolist()
    return dict(items=len(a),rooms=len(rooms),delta_pp=delta,ci95_pp=ci,draws=10000,seed=17,
        estimator='official eight-task macro; direction averages three subtype means; bootstrap physical rooms',
        verdict='REJECT ledger' if ci[1]<-2.5 or ci[0]>2.4 else 'Ledger not rejected')

def direct_rules(leg,parent,f17=None,dev858=None):
    index(leg);index(parent)
    select=lambda rs:[r for r in rs if r['stratum']=='primary']
    route=lambda rs:[r for r in rs if r['question_type']=='route_planning']
    result={'leg_minus_parent':{'primary':comparison(select(leg),select(parent),'released_answer'),
                               'route_own_labels':comparison(route(leg),route(parent),'answer')}}
    equal=all(v['delta_pp']==0 and v['ci95_pp']==[0.0,0.0] for v in result['leg_minus_parent']['primary']['per_type'].values())
    equal=equal and result['leg_minus_parent']['route_own_labels']['overall']['ci95_pp']==[0.0,0.0]
    result['parent_verdict']='no difference from the parent' if equal else 'Scores differ from the parent; see paired intervals.'
    result['changes_against_parent']={t:dict(leg=aggregate([r for r in leg if r['question_type']==t],
        'answer' if t=='route_planning' else 'released_answer'),parent=aggregate([r for r in parent if r['question_type']==t],
        'answer' if t=='route_planning' else 'released_answer')) for t in sorted({r['question_type'] for r in leg})}
    cap=100*sum(r['capped'] for r in leg)/len(leg)
    result['caps_per_100']=cap
    result['caps_by_type']={t:100*sum(r['capped'] for r in leg if r['question_type']==t)/sum(r['question_type']==t for r in leg) for t in sorted({r['question_type'] for r in leg})}
    failures=[]
    if f17 is not None:
        result['leg_minus_f17']={'primary':comparison(select(leg),select(f17),'released_answer'),
                                  'route_own_labels':comparison(route(leg),route(f17),'answer')}
        failures=below_zero(result['leg_minus_f17']['primary'])+below_zero(result['leg_minus_f17']['route_own_labels'])
    result['m100_reversal']=('STOP at m100 and reopen the lineage: '+', '.join(failures) if failures else
        'INCOMPLETE: f17 dev-S1 comparison is missing' if f17 is None else 'PASS: no direct task has a wholly negative paired interval against f17')
    r3bad=failures or cap>1
    if dev858 is not None:
        a,b=dev858; c=comparison(a,b,'released_answer'); result['dev858']=c
        result['dev858_caps_per_100']=100*sum(r['capped'] for r in a)/len(a)
        r3bad=r3bad or below_zero(c) or result['dev858_caps_per_100']>1
    result['R3']=('FAIL: raise direct share or shorten the thinking budget at the next boundary' if r3bad else
        'INCOMPLETE: need f17 dev-S1 and paired dev-858 reads' if f17 is None or dev858 is None else 'PASS')
    return result

def facing(away,forward,pairs):
    aa,ff=index(away),index(forward)
    if set(aa)!={'devrows:'+p['away_id'] for p in pairs} or set(ff)!={'devrows:'+p['forward_id'] for p in pairs}:
        raise ValueError('Facing-away pair membership differs')
    result={}
    for typ in sorted({p['question_type'] for p in pairs}):
        ps=[p for p in pairs if p['question_type']==typ]; ar=[];fr=[];cats=Counter()
        for p in ps:
            a,f=aa['devrows:'+p['away_id']],ff['devrows:'+p['forward_id']]
            if a['room']!=f['room'] or a['room']!=p['room']: raise ValueError('Pair room differs')
            ar.append(a);fr.append(f);cats[f"forward_{int(f['scores']['answer'])}_away_{int(a['scores']['answer'])}"]+=1
        def constants(rs):
            labels=Counter();pred=Counter()
            for r in rs:
                opts={chr(65+i):str(v).split('. ',1)[-1].strip().lower() for i,v in enumerate(r['options'])}
                labels[opts.get(str(r['answer']).strip(),str(r['answer']).strip().lower())]+=1
                raw=str(r.get('prediction','')).strip()
                pred[opts.get(raw,raw.lower())]+=1
            return dict(always_answer_accuracy_pct={k:100*v/len(rs) for k,v in sorted(labels.items())},
                predicted_answer_pct={k:100*v/len(rs) for k,v in sorted(pred.items())},
                majority_constant_accuracy_pct=100*max(labels.values())/len(rs))
        result[typ]=dict(away=aggregate(ar,'answer'),forward=aggregate(fr,'answer'),pair_outcomes=dict(cats),
                         away_constants=constants(ar),forward_constants=constants(fr))
    return result

def routed_rules(arms,table,raised=(),step=100,expected_types=None):
    required={'forced_route','scripted','forced_direct','unflagged'}
    if set(arms)!=required: raise ValueError('Routed report needs all four arms')
    idx={a:index(rs) for a,rs in arms.items()}
    keys=set(idx['forced_route'])
    if any(set(x)!=keys for x in idx.values()): raise ValueError('Routed arm membership differs')
    for k in keys:
        same=[(x[k]['room'],x[k]['question_type'],x[k]['perception_identity'],x[k]['checkpoint_sha256']) for x in idx.values()]
        if len(set(same))!=1: raise ValueError('Routed arms must share checkpoint/perception/physical room')
    out={}; present={r['question_type'] for r in arms['unflagged']}
    for t in sorted(present):
        data={a:[r for r in rs if r['question_type']==t] for a,rs in arms.items()}
        label='released_answer' if all(r['stratum']=='primary' for r in data['unflagged']) else 'answer'
        score=lambda a:aggregate(data[a],label)['score_pct']
        route=table.get(t,'direct')=='route'
        forced='forced_route' if route else 'forced_direct'
        n=len(data[forced]); path=sum(bool(r['called'])==route for r in data['unflagged'])/n
        gap=score('unflagged')-score(forced)
        row=dict(path_match_pct=100*path,unflagged_minus_forced_pp=gap,R1b='PASS' if path>=.95 and abs(gap)<=2 else 'FAIL: revisit path-choice training')
        if route:
            rate=sum(r['called'] for r in data['forced_route'])/n
            errors=sum(r['call_errors']+r['version_errors'] for a in ('forced_route','scripted') for r in data[a])
            gap=score('forced_route')-score('scripted')
            fail=abs(gap)>5 or rate<.95 or errors>0
            row.update(call_rate_pct=100*rate,call_or_version_errors=errors,routed_minus_scripted_pp=gap,
                R1=('STOP at m200: this type still fails after rows were raised at m100' if fail and step==200 and t in raised else
                    'FAIL: send this form more rows at the next boundary' if fail else 'PASS'))
            c=paired(data['forced_route'],data['forced_direct'],label);lo,hi=c['ci95_pp']
            row['routed_minus_direct']=c
            row['R2']='PASS: routing wins' if lo>0 else 'FAIL: move this type to direct at the next boundary' if hi<0 else 'INCONCLUSIVE: keep the frozen table and log this cell'
        out[t]=row
    expected=set(table) if expected_types is None else set(expected_types)
    return dict(per_type=out,missing_types=sorted(expected-present),
                completeness='COMPLETE' if expected<=present else 'INCOMPLETE: missing table types')

def write_report(args):
    l=load_merge(args.leg); p=load_merge(args.parent,expected_model='cp1m200')
    if not args.parent_standin and not l['model'].startswith('LEG-S1-m'): raise ValueError('LEG input is not a bound LEG export')
    if not args.parent_standin and l.get('checkpoint',{}).get('step')!=args.step: raise ValueError('Decision step differs from checkpoint')
    if p['artifact']['sha256']!=PARENT_SHA: raise ValueError('Wrong parent artifact')
    if args.parent_standin and l['artifact']['sha256']!=PARENT_SHA: raise ValueError('Stand-in must be the parent')
    f=load_merge(args.f17,'ON16k',expected_model='f17') if args.f17 else None
    if f and f['artifact']['sha256']!='47308d99246bdf253a5d55ce9ec04a38a4fcc355092603a51e8de34604749eae':raise ValueError('Wrong f17 artifact')
    if any(v['strata_sha256']!=l['strata_sha256'] for v in (p,f) if v): raise ValueError('Comparator strata differ')
    d858=None
    if args.dev858:
        from auxiliary import admit
        d=admit(args.dev858,l['artifact']['sha256'],858); d858=(d['leg'],d['f17'])
        if len(d858[0])!=858 or len(d858[1])!=858: raise ValueError('dev858 requires exactly 858 paired items')
    result=direct_rules(l['rows'],p['rows'],f['rows'] if f else None,d858)
    lon,pon=load_merge(args.leg,'ON16k'),load_merge(args.parent,'ON16k',expected_model='cp1m200')
    select_route=lambda x:[r for r in x['rows'] if r['question_type']=='route_planning']
    result['route_ON16k_disclosure']=dict(leg=aggregate(select_route(lon),'answer'),parent=aggregate(select_route(pon),'answer'),
        leg_minus_parent=comparison(select_route(lon),select_route(pon),'answer'),
        note='The card parent 29.33% is ON16k. Primary decision protocol B2048 gives parent route 33.33%. Never mix these arms.')
    if f:result['route_ON16k_disclosure']['leg_minus_f17']=comparison(select_route(lon),select_route(f),'answer')
    result.update(step=args.step,parent_standin=args.parent_standin,inputs={k:pin(v) for k,v in
        [('leg',Path(args.leg)/'MERGE_COMPLETE.json'),('parent',Path(args.parent)/'MERGE_COMPLETE.json')]},
        report_scope='CPU parent stand-in; cannot authorize a training decision' if args.parent_standin else 'registered boundary read')
    if bool(args.away)!=bool(args.forward): raise ValueError('Both facing-away arms required')
    if args.away:
        away,forward=load_merge(args.away),load_merge(args.forward)
        if any(x['artifact']!=l['artifact'] for x in (away,forward)): raise ValueError('Facing checkpoint differs')
        result['facing_away']=facing(away['rows'],forward['rows'],rows(VENDOR/'r4/PAIRS.jsonl'))
    else: result['facing_away']='INCOMPLETE: need both control cells'
    if args.routed:
        bundle=load(checked(load(args.routed)))
        import routed
        for name,receipt_pin in bundle['receipts'].items():
            receipt=load(checked(receipt_pin)); request=routed.validate_request(load(checked(receipt['request'])),live=True)
            native=rows(checked(receipt['journal']))
            if not load(checked(receipt['parity']))['pass']:raise ValueError('Routed parity missing')
            if native!=bundle['arms'][name] or request['arm']!=name:raise ValueError('Routed bundle differs from authenticated journal')
            if request['step']!=args.step or request['artifact']['sha256']!=l['artifact']['sha256']:raise ValueError('Routed checkpoint differs from direct checkpoint')
        raised=load(args.history)['rows_raised_at_m100'] if args.history else []
        result['routed']=routed_rules(bundle['arms'],load(ROOT/'out/ROUTING_POLICY.json'),raised,args.step,
            expected_types={t['question_type'] for t in rows(VENDOR/'r3/TASKS.jsonl')})
        result['routed']['qualification']='UNQUALIFIED: development prompt controls are not bound to trained flags; numerical verdicts cannot certify registered R1b'
    else: result['routed']='INCOMPLETE: routed journals missing'
    if args.official:
        from auxiliary import admit
        d=admit(args.official,l['artifact']['sha256'],5130);result['official_ledger']=official_ledger(d['leg'],d['f17'])
        result['official_ledger']['route_planning']=comparison([r for r in d['leg'] if r['question_type']=='route_planning'],
            [r for r in d['f17'] if r['question_type']=='route_planning'],'released_answer')
        result['official_ledger']['term_checks']='INCOMPLETE: require forced-direct official absolute-distance and room-size reads outside ARKitScenes'
        if 'forced_direct' in d:
            select=lambda rs,t:[r for r in rs if r['question_type']==t and r['dataset'] not in ('arkitscenes','d3')]
            result['official_ledger']['term_checks']={t:paired(select(d['leg'],t),select(d['forced_direct'],t),'released_answer')
                for t in ('object_abs_distance','room_size_estimation')}
    elif args.step==200: result['official_ledger']='INCOMPLETE: official ledger comparison missing'
    if args.step==200 and not args.history:result['m200_rows_history']='INCOMPLETE: require the recorded types whose rows were raised at m100'
    dump(args.output,result)
    lines=[result['parent_verdict'],result['m100_reversal'],'R3: '+result['R3'],
           'Routed: '+(result['routed'] if isinstance(result['routed'],str) else result['routed']['completeness']),
           '', '| Type | LEG % | Parent % | Change (pp) | LEG caps/100 |','|---|---:|---:|---:|---:|']
    for t,x in result['changes_against_parent'].items():
        a,b=x['leg'],x['parent']; lines.append(f"| {t} | {a['score_pct']:.4f} | {b['score_pct']:.4f} | {a['score_pct']-b['score_pct']:+.4f} | {a['caps_per_100']:.2f} |")
    for name in ('leg_minus_parent','leg_minus_f17'):
        if name not in result:continue
        lines+=['',name.replace('_',' ')+'. Bootstrap over physical rooms; 10,000 draws, seed 17.',
            '', '| Stratum / type | Items | Rooms | Difference (pp) | 95% interval (pp) |',
            '|---|---:|---:|---:|---:|']
        for stratum,c in result[name].items():
            for typ,r in [('overall',c['overall']),*c['per_type'].items()]:
                if r['ci95_pp'] is not None:lines.append(f"| {stratum} / {typ} | {r['items']} | {r['rooms']} | {r['delta_pp']:+.4f} | [{r['ci95_pp'][0]:+.4f}, {r['ci95_pp'][1]:+.4f}] |")
    if isinstance(result['facing_away'],dict):
        lines+=['','Facing-away controls use own labels. Constant-answer rates map option letters back to meanings.',
            '', '| Type | Away % | Forward % | Best away constant % | Best forward constant % |', '|---|---:|---:|---:|---:|']
        for typ,r in result['facing_away'].items():
            lines.append(f"| {typ} | {r['away']['score_pct']:.2f} | {r['forward']['score_pct']:.2f} | {r['away_constants']['majority_constant_accuracy_pct']:.2f} | {r['forward_constants']['majority_constant_accuracy_pct']:.2f} |")
            lines+=['',typ+' answer frequencies: '+json.dumps({side:r[side+'_constants']['predicted_answer_pct'] for side in ('away','forward')},sort_keys=True),
                    'Paired outcomes: '+json.dumps(r['pair_outcomes'],sort_keys=True)]
    if isinstance(result['routed'],dict):
        lines+=['',result['routed']['qualification'],'','Routed verdicts:']
        for typ,r in result['routed']['per_type'].items():
            lines+=['',typ+': '+'; '.join(k+' '+r[k] for k in ('R1','R1b','R2') if k in r)]
    lines+=['',result['route_ON16k_disclosure']['note'],
        f"ON16k route scores: LEG {result['route_ON16k_disclosure']['leg']['score_pct']:.4f}%, parent {result['route_ON16k_disclosure']['parent']['score_pct']:.4f}%."]
    Path(args.output).with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines[:4]))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('leg','parent','output'):p.add_argument('--'+k,required=True)
    for k in ('f17','away','forward','dev858','routed','history','official'):p.add_argument('--'+k)
    p.add_argument('--step',type=int,choices=[100,200],required=True);p.add_argument('--parent-standin',action='store_true')
    write_report(p.parse_args())
if __name__=='__main__':main()
