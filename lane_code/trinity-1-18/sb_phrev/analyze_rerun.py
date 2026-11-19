"""Independent policy selection and score aggregation of freshly rebuilt pools."""
import collections, gzip, hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT.parent/'sb_mask_phrase'
PINS={}
EXCLUDED={'scannet/'+c for c in ['scene0201_02','scene0478_00','scene0478_01','scene0614_02','scene0692_03']}
def read(p):
    p=Path(p);b=p.read_bytes();PINS[str(p)]=hashlib.sha256(b).hexdigest();return b
def js(p):return json.loads(read(p))
def mra(pred,truth):
    return 0. if pred is None else float(np.mean(abs(pred-truth)/abs(truth)<1-np.arange(.5,.96,.05)))
def contrast(left,right):
    a={r['row_id']:r for r in left};b={r['row_id']:r for r in right};assert a.keys()==b.keys()
    ids=sorted(a);rooms=sorted({a[i]['room'] for i in ids});ri={r:k for k,r in enumerate(rooms)}
    x=np.array([mra(a[i]['prediction'],a[i]['label']) for i in ids]);y=np.array([mra(b[i]['prediction'],b[i]['label']) for i in ids])
    assert all(a[i]['label']==b[i]['label'] and a[i]['room']==b[i]['room'] for i in ids)
    cl=[ri[a[i]['room']] for i in ids];s=np.bincount(cl,weights=x-y,minlength=len(rooms));n=np.bincount(cl,minlength=len(rooms))
    draws=np.random.default_rng(20261119).integers(0,len(rooms),(10000,len(rooms)))
    lohi=np.percentile(100*s[draws].sum(1)/n[draws].sum(1),[2.5,97.5]).tolist()
    return dict(rows=len(ids),rooms=len(rooms),left_mra=float(100*x.mean()),right_mra=float(100*y.mean()),delta=float(100*(x-y).mean()),ci95=lohi)
def choose(objects,arm,held):
    fit=[o for o in objects if held is None or o['fold']!=held]
    prefix={'W1':'q:','W2':'fb:','W2c':'call:'}[arm]
    variants=['raw']+[prefix+a for a in objects[0]['aliases']]
    counts={v:sum(o['keys'][o['variants'][v]]['on_target'] for o in fit) for v in variants}
    selected=max(variants,key=lambda v:counts[v]) if len(fit)>=5 else 'raw'
    return selected,dict(fit_objects=len(fit),counts=counts,fit_captures=sorted(o['capture'] for o in fit))
def policies(objects):
    grouped=collections.defaultdict(list)
    for o in objects:grouped[o['name']].append(o)
    choices={};evidence={}
    for arm in ['W1','W2','W2c']:
        choices[arm]={};evidence[arm]={}
        for f in [0,1,2,3,4,None]:
            key=str(f) if f is not None else 'all_rooms'
            ce={n:choose(os,arm,f) for n,os in sorted(grouped.items())}
            choices[arm][key]={n:v[0] for n,v in ce.items()}
            evidence[arm][key]={n:v[1] for n,v in ce.items()}
    return choices,evidence
def assemble(data,choices):
    out={a:[] for a in ['P0','W1','W2','W2c']}
    for d in data:
        lookup={(r['row_id'],tuple(r['keys'].items())):r for r in d['items']}
        for arm in out:
            for row in d['rows']:
                variants={n:'raw' if arm=='P0' else choices[arm][str(d['fold'])][n] for n in row['operands']}
                keys={n:d['names'][n]['variants'][v] for n,v in variants.items()}
                out[arm].append(dict(lookup[(row['id'],tuple(keys.items()))],arm=arm,variants=variants))
    return out
def main():
    read(__file__);read(ROOT/'run_review.sh')
    files=sorted((ROOT/'rerun_caps').glob('*.json.gz'));assert len(files)==209,len(files)
    data=[json.loads(gzip.decompress(read(p))) for p in files]
    pub=[json.loads(line) for line in read(SRC/'out/PER_ITEM.jsonl').splitlines()]
    a0=[json.loads(line) for line in read(ROOT.parent/'sb_kbox4/out/box_ladder/PER_ITEM.jsonl').splitlines()]
    a0=[r for r in a0 if r['arm']=='A0_deployed']
    dec=js(SRC/'out/DECISION.json'); objs=[]
    for d in data:
        assert d['k1_split']=='train'
        for name,o in d['names'].items():objs.append(dict(o,name=name,fold=d['fold'],capture=d['capture'],room=d['room']))
    choices,ev=policies(objs);arms=assemble(data,choices)
    policy_mismatch=[]
    for arm in choices:
        for fold,ns in choices[arm].items():
            for name,v in ns.items():
                if v!=dec['fold_choices'][arm][fold].get(name,'raw'):policy_mismatch.append((arm,fold,name,v))
    good={r['id'] for d in data for r in d['rows'] if all(d['names'][n]['keys'][d['names'][n]['variants']['raw']]['on_target'] for n in r['operands'])}
    idx={r['row_id']:r for r in a0}
    def report(rows):
        base=[idx[r['row_id']] for r in rows];safe=[r for r in rows if r['row_id'] in good]
        gain=contrast(rows,base);s=contrast(safe,[idx[r['row_id']] for r in safe])
        return dict(gain=gain,safe=s,phrase_worth=gain['delta']>=1.5 and gain['ci95'][0]>0,phrase_safe=s['ci95'][0]>-1,
                    refusals=sum(r['prediction'] is None for r in rows))
    comparisons={}
    fields=['prediction','box','member_frames','refusal_code','label','room']
    for arm,rows in arms.items():
        old={r['row_id']:r for r in pub if r['arm']==arm}
        comparisons[arm]={field:sum(r[field]==old[r['row_id']][field] for r in rows) for field in fields}
    parity={field:sum(r[field]==idx[r['row_id']][field] for r in arms['P0']) for field in fields}
    excluded_rows=[r for r in arms['W1'] if r['capture'] in EXCLUDED]
    clean=[d for d in data if d['capture'] not in EXCLUDED]
    cleanchoices,cleanev=policies([o for o in objs if o['capture'] not in EXCLUDED]);cleanarms=assemble(clean,cleanchoices)
    changed_policy=[(a,f,n,v,cleanchoices[a][f][n]) for a in choices for f in choices[a] for n,v in choices[a][f].items() if n in cleanchoices[a][f] and v!=cleanchoices[a][f][n]]
    heater=[r for r in arms['W1'] if 'heater' in r['keys']]
    changed=[r for r in arms['W1'] if r['prediction']!=idx[r['row_id']]['prediction']]
    checks=[c for d in data for c in d['checks']]
    rooms=collections.defaultdict(set)
    for d in data:rooms[d['room']].add(d['fold'])
    out=dict(command='bash run_review.sh analyze_rerun.py',rebuild_command='bash run_review.sh rerun.py',
             captures=len(data),objects=len(objs),rows=len(arms['W1']),parity=parity,published_comparison=comparisons,
             policy_mismatches=policy_mismatch,fold_choices={a:{f:{n:v for n,v in ns.items() if v!='raw'} for f,ns in folds.items()} for a,folds in choices.items()},
             fold_evidence=ev,room_fold_conflicts={r:list(fs) for r,fs in rooms.items() if len(fs)>1},
             reports={a:report(rs) for a,rs in arms.items()},
             by_dataset={ds:report([r for r in arms['W1'] if r['dataset']==ds]) for ds in ['arkitscenes','scannet','scannetpp']},
             heater=dict(rows=len(heater),captures=len({r['capture'] for r in heater}),gain=contrast(heater,[idx[r['row_id']] for r in heater]),
                         changed_predictions=len(changed),nonheater_changed_predictions=sum('heater' not in r['keys'] for r in changed)),
             exclusion=dict(captures=sorted(EXCLUDED),rows=len(excluded_rows),row_ids=[r['row_id'] for r in excluded_rows],
                            heater_rows=sum('heater' in r['keys'] for r in excluded_rows),
                            retained_report=report([r for r in arms['W1'] if r['capture'] not in EXCLUDED]),
                            refit_retained_report=report(cleanarms['W1']),refit_policy_changes=changed_policy,
                            refit_fold_evidence=cleanev['W1']),
             checks=dict(pools=len(checks),survival_failures=sum(not c['survival'] for c in checks),
                         identity_failures=sum(not c['identities'] for c in checks),reader_refusals=sum(len(d['reader_refused']) for d in data),
                         raw_builder_failures=sum(not c['passed'] for d in data for c in d['builder_parity']),
                         fresh_raw_labels_match=sum(c['table'] is True for c in checks)),
             input_sha256=PINS)
    (ROOT/'RERUN_AUDIT.json').write_text(json.dumps(out,indent=1)+'\n')
    short={k:out[k] for k in ['captures','objects','rows','parity','published_comparison','policy_mismatches','reports','by_dataset','heater','checks']}
    short['exclusion']={k:v for k,v in out['exclusion'].items() if k not in ['row_ids','refit_fold_evidence']}
    print(json.dumps(short,indent=1))
if __name__=='__main__':main()
