"""Room-cross-fitted training selection, paired contrasts and registered bars."""
import collections,hashlib,itertools,json,sys
import numpy as np
from serving_reference import ROOT,OUT,read,write,PINS,code_pins,ROWSETS
import math_v2 as M

VARIANTS=[(t,r,f'A4_obj_{t:.2f}_{r}') for t in M.TAUS for r in M.RULES]

def load(phase):
    items=[];pins={}
    paths=sorted((OUT/phase).glob('*.json'))
    assert len(paths)==209,(phase,len(paths))
    for p in paths:
        rec=json.loads(read(p));PINS.update(rec['input_sha256']);pins[str(p)]=PINS[str(p)]
        assert rec['phase']==phase
        for r in rec['items']:
            assert r['split']=='train';r['source_file']=str(p);items.append(r)
    return items

def byarm(items):
    arms=collections.defaultdict(list)
    for r in items:arms[r['arm']].append(r)
    return dict(arms)

def objects(rows):
    out={}
    for r in rows:
        for name,d in r['diagnostics'].items():
            key=(r['capture'],d['instance'])
            value=dict(d,capture=r['capture'],room=r['room'],fold=r['fold'],name=name)
            if key in out:
                # A Session can refuse a pair while still returning one valid operand box.
                assert out[key]['first_gt']==value['first_gt'] and out[key]['gt_longest']==value['gt_longest']
                if out[key]['printed_longest'] is not None and value['printed_longest'] is not None:
                    assert out[key]['printed_longest']==value['printed_longest']
                if out[key]['printed_longest'] is None and value['printed_longest'] is not None:out[key]=value
            else:out[key]=value
    return list(out.values())

def precision(rows):
    obs=objects(rows);n=sum(o.get('added',0) for o in obs);hit=sum(o.get('correct',0) for o in obs)
    return dict(added=n,correct=hit,precision=hit/n if n else None)

def mean(rows):return 100*float(np.mean([M.mra(r['prediction'],r['label']) for r in rows]))

def contrast(left,right):
    a,b=({r['row_id']:r for r in rows} for rows in (left,right));assert set(a)==set(b)
    ids=sorted(a);rooms=sorted({a[i]['room'] for i in ids});idx={r:k for k,r in enumerate(rooms)}
    assert all(a[i]['room']==b[i]['room'] and a[i]['label']==b[i]['label'] for i in ids)
    delta=np.array([M.mra(a[i]['prediction'],a[i]['label'])-M.mra(b[i]['prediction'],b[i]['label']) for i in ids]);clusters=[idx[a[i]['room']] for i in ids]
    sums=np.bincount(clusters,weights=delta,minlength=len(rooms));counts=np.bincount(clusters,minlength=len(rooms))
    draws=np.random.default_rng(20261119).integers(0,len(rooms),(10000,len(rooms)))
    boot=sums[draws].sum(1)/counts[draws].sum(1)
    both=[i for i in ids if a[i]['prediction'] is not None and b[i]['prediction'] is not None]
    diagnostic=dict(rows=len(both),left_mra=mean([a[i] for i in both]) if both else None,right_mra=mean([b[i] for i in both]) if both else None,role='diagnostic only; never a bar')
    return dict(rows=len(ids),rooms=len(rooms),left_mra=mean(left),right_mra=mean(right),estimate=float(100*delta.mean()),ci95=(100*np.percentile(boot,[2.5,97.5])).tolist(),draws=10000,seed=20261119,both_answered=diagnostic)

def choose(arms,excluded=None,gt=False):
    choices=[]
    variants=[(None,r,'A3_gt_fused_'+r) for r in M.RULES if r!='best1'] if gt else VARIANTS
    for tau,rule,arm in variants:
        rows=[r for r in arms[arm] if r['fold']!=excluded]
        pr=precision(rows)
        if gt or pr['precision'] is None or pr['precision']>=.90:choices.append((mean(rows),tau,rule,arm,pr))
    if not choices:return None
    value=max(x[0] for x in choices)
    winner=next(x for x in choices if x[0]==value)
    return dict(tau=winner[1],rule=winner[2],arm=winner[3],selection_train_mra=winner[0],selection_precision=winner[4])

def crossfit(arms,gt=False):
    selected={str(k):choose(arms,k,gt) for k in range(5)};rows=[]
    for k in range(5):
        arm=selected[str(k)]['arm'] if selected[str(k)] else ('A2_gt_masks' if gt else 'A0_deployed')
        rows += [dict(r,arm='fused_cf' if gt else 'obj_cf',chosen_arm=arm) for r in arms[arm] if r['fold']==k]
    return rows,selected

def sizes(rows):
    return [dict(row_id=o['object_id'],room=o['room'],prediction=o['printed_longest'],label=o['gt_longest']) for o in objects(rows)]

def appearance(rows):
    captures=collections.defaultdict(list)
    for o in objects(rows):captures[o['capture']].append(o)
    pairs=[]
    for capture,obs in captures.items():
        for a,b in itertools.combinations(sorted(obs,key=lambda o:o['instance']),2):
            if a['first_gt'] is None or b['first_gt'] is None or a['first_gt']==b['first_gt']:continue
            ok=a['first_printed'] is not None and b['first_printed'] is not None and (a['first_printed']-b['first_printed'])*(a['first_gt']-b['first_gt'])>0
            pairs.append(dict(capture=capture,instances=[a['instance'],b['instance']],correct=ok,fold=a['fold']))
    obs=objects(rows)
    return dict(pairs=len(pairs),correct=sum(p['correct'] for p in pairs),rate=sum(p['correct'] for p in pairs)/len(pairs) if pairs else None,
        objects=len(obs),exact=sum(o['first_printed'] is not None and o['first_printed']==o['first_gt'] for o in obs)/len(obs),
        within_one=sum(o['first_printed'] is not None and o['first_gt'] is not None and abs(o['first_printed']-o['first_gt'])<=1 for o in obs)/len(obs))

def freeze(arms):
    cf,folds=crossfit(arms);gcf,gfolds=crossfit(arms,True)
    obj=choose(arms);fusion=choose(arms,gt=True)
    pr=precision(cf);gain=contrast(cf,arms['A0_deployed']);fgain=contrast(gcf,arms['A2_gt_masks'])
    replace=gain['estimate']>=3 and gain['ci95'][0]>0 and (pr['precision'] is None or pr['precision']>=.9)
    # Freeze the appearance threshold separately when the distance bar fails.
    def first_choice(exclude=None):
        if replace and obj:return obj['tau']
        eligible=[]
        for tau in M.TAUS:
            rows=[r for r in arms[f'A4_obj_{tau:.2f}_best1'] if r['fold']!=exclude];p=precision(rows);a=appearance(rows)
            if p['precision'] is None or p['precision']>=.9:eligible.append((a['rate'] or 0,tau))
        return max(eligible,key=lambda x:x[0])[1] if eligible else None
    ftau=first_choice();first_rows=[];first_folds={}
    for k in range(5):
        tau=(folds[str(k)]['tau'] if replace and folds[str(k)] else first_choice(k))
        arm=f'A4_obj_{tau:.2f}_best1' if tau is not None else 'A0_deployed';first_folds[str(k)]=tau
        first_rows += [dict(r,arm='first_object_cf',chosen_arm=arm) for r in arms[arm] if r['fold']==k]
    result=dict(frozen_variant=obj,fused_frozen=fusion,object_folds=folds,fused_folds=gfolds,
        object_gain=gain,fused_gain=fgain,merge_safe=pr,replace_box_part1=replace,
        appearance_tau=ftau,appearance_folds=first_folds,first_object_cf=appearance(first_rows),
        first_linker=appearance(arms['A0_deployed']),first_object_frozen=appearance(arms[f'A4_obj_{ftau:.2f}_best1']) if ftau else None,
        heldout_evaluated=False,A6_status='DEFERRED')
    return result,cf+gcf+first_rows

def main():
    phase=sys.argv[1];items=load('base');arms=byarm(items)
    rowids=set(read(ROWSETS/'K1_TRAIN_1037.txt').decode().splitlines());tableids=set(read(ROWSETS/'K1_TRAIN_TABLES_883.txt').decode().splitlines())
    for a,rows in arms.items():assert {r['row_id'] for r in rows}==(tableids if a=='A1_oracle_select' else rowids)
    frozen,cf=freeze(arms);code_pins()
    if phase=='freeze':
        write(OUT/'FREEZE.json',frozen)
        (ROOT/'STATUS.md').write_text(f'Training object and GT-mask fusion choices are frozen in out/box_ladder/FREEZE.json. Object gain is {frozen["object_gain"]["estimate"]:.3f} points under room cross-fitting. Non-null selector fitting and dependent report arms remain. No held-out or A6 evaluation ran.\n')
        print(json.dumps(frozen,indent=2));return
    assert phase=='final'
    saved=json.loads(read(OUT/'FREEZE.json'));assert all(saved[k]==v for k,v in frozen.items())
    items+=load('extras');items+=cf;arms=byarm(items)
    if frozen['frozen_variant']:
        items += [dict(r,arm='obj_frozen',chosen_arm=frozen['frozen_variant']['arm']) for r in arms[frozen['frozen_variant']['arm']]]
        arms=byarm(items)
    a0=arms['A0_deployed'];a0t=[r for r in a0 if r['row_id'] in tableids]
    contrasts={'object_cf_minus_A0':frozen['object_gain'],'fused_cf_minus_A2':frozen['fused_gain'],
        'A1_minus_A0_tables':contrast(arms['A1_oracle_select'],a0t),'A2_minus_A0':contrast(arms['A2_gt_masks'],a0),
        'A8_nonull_minus_A0_tables':contrast(arms['A8_nonull_best1'],a0t),
        'size_obj_cf_minus_A0':contrast(sizes(arms['obj_cf']),sizes(a0)),
        'A9_today_minus_A0':contrast(arms['A9_s4_today'],a0)}
    if 'obj_frozen' in arms:
        contrasts['A9_obj_minus_frozen_A4']=contrast(arms['A9_s4_obj'],arms['obj_frozen'])
        contrasts['size_A9_obj_minus_frozen_A4']=contrast(sizes(arms['A9_s4_obj']),sizes(arms['obj_frozen']))
        contrasts['A5_minus_A1_tables']=contrast(arms['A5_obj_oracle_seed'],arms['A1_oracle_select'])
    for name in ['da3','pi3x']:
        if not frozen['frozen_variant']:continue
        rule=frozen['frozen_variant']['rule'] if frozen['frozen_variant'] else 'best1'
        ref='A2_gt_masks' if rule=='best1' else 'A3_gt_fused_'+rule
        contrasts['A7_'+name+'_minus_GD_frozen']=contrast(arms['A7_'+name+'_frozen'],arms[ref])
    p=frozen['merge_safe']['precision'];sz=contrasts['size_obj_cf_minus_A0'];sel=contrasts['A8_nonull_minus_A0_tables']
    decisions=dict(replace_box=dict(verdict='PASS' if frozen['replace_box_part1'] else 'FAIL',scope='part 1 only; tower_frames part 2 required',evidence=frozen['object_gain']),
        fused_path=dict(verdict='PASS' if frozen['fused_gain']['estimate']>=3 and frozen['fused_gain']['ci95'][0]>0 else 'FAIL',evidence=frozen['fused_gain']),
        merge_safe=dict(verdict='NA' if p is None else 'PASS' if p>=.9 else 'FAIL',evidence=frozen['merge_safe']),
        selector_worth=dict(verdict='PASS' if contrasts['A1_minus_A0_tables']['estimate']>=4 else 'FAIL',evidence=contrasts['A1_minus_A0_tables']),
        selector_adopt=dict(verdict='PASS' if sel['ci95'][0]>0 else 'FAIL',evidence=sel,primary_arm='A8_nonull_best1; fixed before scoring'),
        size_screen=dict(verdict='PASS' if sz['estimate']>=5 and sz['ci95'][0]>0 else 'FAIL',evidence=sz),
        first_seen_screen=dict(verdict='PASS' if max(frozen['first_linker']['rate'] or 0,frozen['first_object_cf']['rate'] or 0)>=.9 else 'FAIL',linker=frozen['first_linker'],object_oof=frozen['first_object_cf'],object_frozen=frozen['first_object_frozen']),
        tower_challenger=dict(verdict='REPORT_ONLY',evidence={k:v for k,v in contrasts.items() if k.startswith('A7')}))
    if frozen['fused_gain']['estimate']<1:decisions['fused_path']['interpretation']='the single view is not the limit under this tower'
    summary={a:dict(rows=len(rs),rooms=len({r['room'] for r in rs}),mra=mean(rs),refusals=sum(r['prediction'] is None for r in rs),size_mra=mean(sizes(rs)),objects=len(objects(rs)),precision=precision(rs),first_seen=appearance(rs),
        ci95=contrast(rs,[dict(r,prediction=None) for r in rs])['ci95'],
        selection='cross-fitted' if a in ('obj_cf','fused_cf','first_object_cf') else 'OOF selector' if a.startswith('A8') else 'in-sample') for a,rs in arms.items()}
    bands={}
    for a,rs in arms.items():
        subsets=collections.defaultdict(list)
        for r in rs:
            subsets['dataset/'+r['dataset']].append(r)
            truth=r['label'];band='<1' if truth<1 else '1-2' if truth<2 else '2-4' if truth<=4 else '>4';subsets['truth/'+band].append(r)
            n=min(map(len,r['member_frames'].values()));subsets['min_frames/'+('0' if n==0 else '1' if n==1 else '2' if n==2 else '3-4' if n<=4 else '5+')].append(r)
        bands[a]={k:dict(rows=len(v),mra=mean(v),refusals=sum(r['prediction'] is None for r in v)) for k,v in subsets.items()}
    write(OUT/'DECISION.json',dict(bars=decisions,freeze=frozen,rowsets=dict(train=sorted(rowids),tables=sorted(tableids)),heldout_status='DEFERRED; no read',A6_status='DEFERRED by order 0654Z'))
    write(OUT/'SUMMARY_TRAIN.json',dict(arms=summary,contrasts=contrasts,bands=bands))
    write(OUT/'OBJECT_DIAGNOSTICS.json',dict(arms={a:objects(rs) for a,rs in arms.items()}))
    with (OUT/'PER_ITEM.jsonl').open('w') as f:
        for r in items:
            source=r.pop('source_file');r['input_sha256']={source:PINS[source],str(OUT/'FREEZE.json'):PINS[str(OUT/'FREEZE.json')]}
            f.write(json.dumps(r,allow_nan=False)+'\n')
    lines=['K1 TRAINING ONLY; every refusal scores zero; every variant mean is in-sample unless marked cross-fitted.',
        'All contrasts use identical registered rows; 10,000 physical-room bootstrap draws, seed 20261119.',
        'Arm | Rows | MRA [95% CI] | Refusals | Size MRA | Selection']
    lines += [f'{a} | {s["rows"]} | {s["mra"]:.4f} [{s["ci95"][0]:.4f}, {s["ci95"][1]:.4f}] | {s["refusals"]} | {s["size_mra"]:.4f} | {s["selection"]}' for a,s in sorted(summary.items())]
    lines+=['','Contrast | Rows | Delta | Paired 95% CI']+[f'{k} | {v["rows"]} | {v["estimate"]:+.4f} | [{v["ci95"][0]:+.4f}, {v["ci95"][1]:+.4f}]' for k,v in contrasts.items()]
    lines+=['','Bar | Verdict']+[f'{k} | {v["verdict"]}' for k,v in decisions.items()]
    lines+=['','Both-answered diagnostic | Rows | Left MRA | Right MRA']+[f'{k} | {v["both_answered"]["rows"]} | {v["both_answered"]["left_mra"]} | {v["both_answered"]["right_mra"]}' for k,v in contrasts.items()]
    (OUT/'LADDER_TRAIN.txt').write_text('\n'.join(lines)+'\n')
    (ROOT/'STATUS.md').write_text('Training pricing and room-cross-fitted decisions are complete. out/box_ladder/LADDER_TRAIN.txt contains all variant means and paired contrasts; DECISION.json freezes every choice. Held-out and A6 remain deferred. Final audit and archive remain.\n')
    print('\n'.join(lines[-25:]))

if __name__=='__main__':main()
