#!/usr/bin/env python3
"""Score a preregistered counting comparison under the K1 training freeze."""
import argparse, collections, gzip, json, math, os, random, sys
from pathlib import Path
import numpy as np
import count_guard as G
from official_vsi_mra import official_mra
SEED, DRAWS = 20261119, 10000

def mra(pred, truth):
    try: p, t = float(pred), float(truth)
    except (TypeError, ValueError): return 0.0
    return official_mra(p, t)

def rle_decode(r):
    h, w = r['size']; counts = r['counts']
    if sum(counts) != h * w: raise ValueError('invalid RLE')
    return np.repeat(np.arange(len(counts)) % 2, counts).astype(bool).reshape((h, w), order='F')


def spearman(x, y):
    def rank(v):
        v = np.asarray(v, float); o = np.argsort(v, kind='mergesort'); r = np.empty(len(v)); r[o] = np.arange(len(v), dtype=float)
        for u in np.unique(v):
            m = v == u; r[m] = r[m].mean()
        return r
    if len(x) < 3: return None
    rx, ry = rank(x), rank(y)
    if rx.std() == 0 or ry.std() == 0: return None
    return float(np.corrcoef(rx, ry)[0, 1])


def boot(vals_by_room, draws=DRAWS, seed=SEED):
    rooms = sorted(vals_by_room); rng = random.Random(seed); out = []
    for _ in range(draws):
        s = [v for r in rng.choices(rooms, k=len(rooms)) for v in vals_by_room[r]]
        out.append(sum(s) / len(s))
    out.sort(); return out[int(0.025 * draws)], out[int(0.975 * draws)]

def frame_count(instances, rule=None):
    r = rule or G.config()['rule']
    ins = sorted((i for i in instances if i['joint_score'] >= r['joint']), key=lambda i: -i['joint_score'])
    if not r['nms']: return len(ins)
    kept = []
    for i in ins:
        m = rle_decode(i['mask'])[::r['stride'], ::r['stride']]; a = int(m.sum())
        if not a: continue
        if any((lambda z,b: z and (z / float(a+b-z) > r['iou'] or z / float(min(a,b)) > r['contain']))(int((m & q).sum()),b) for q,b in kept): continue
        kept.append((m,a))
    return len(kept)

def tool_count(teacher, category, rule=None):
    r = rule or G.config()['rule']; per = []
    for slot in sorted(teacher['frames'], key=int):
        ph = teacher['frames'][slot]['phrases'].get(category)
        if ph is None: return None
        per.append(frame_count(ph['instances'], r))
    if len(per) != 32: raise ValueError('expected 32 frame slots')
    order = sorted(range(32), key=lambda k: -per[k])
    best = order[1] if r['kind']=='second' and per[order[1]]>0 else order[0]
    return per[best], best, per

def summarize(items, est, tag=None):
    cfg=G.config();const=cfg['best_const'];res={}
    groups={'large_R0-dev':[x for x in items if x['set']=='R0-dev' and x['truth']>=5],
            'large_dev-S1':[x for x in items if x['set']=='dev-S1' and x['truth']>=5],
            'every_item':items}
    for b in (1,2,3,4):groups['truth_'+str(b)]=[x for x in items if x['truth']==b]
    for name,sel in groups.items():
        if not sel:continue
        scores={'N_tool':[mra(est[x['id']],x['truth']) for x in sel],
                'direct_S1_544':[mra(x['direct']['S1_544']['pred'],x['truth']) for x in sel],
                'frozen_const':[mra(const,x['truth']) for x in sel]}
        d={k:100*sum(v)/len(v) for k,v in scores.items()}
        d.update(n=len(sel),rooms=len({x['room'] for x in sel}),frozen_const_value=const,
                 spearman_tool_truth=spearman([est[x['id']] for x in sel],[x['truth'] for x in sel]),
                 tool_zero=sum(est[x['id']]==0 for x in sel),tool_under=sum(est[x['id']]<x['truth'] for x in sel),tool_over=sum(est[x['id']]>x['truth'] for x in sel))
        by=collections.defaultdict(list)
        for j,x in enumerate(sel):by[x['room']].append(100*(scores['N_tool'][j]-scores['direct_S1_544'][j]))
        lo,hi=boot(by);d['N_tool_minus_direct_S1_544']=[d['N_tool']-d['direct_S1_544'],lo,hi]
        res[name]=d
    return res

def verdict(res):
    cfg=G.config()
    if cfg['training_decision']!='ACCEPT_FOR_COMPARISON':return 'REJECT_ON_TRAINING'
    g=res.get('large_R0-dev')
    if not g:return 'DIAGNOSTIC_ONLY'
    return 'ACCEPT' if g['N_tool']>g['direct_S1_544'] and g['N_tool']>=g['frozen_const'] and g['N_tool_minus_direct_S1_544'][1]>0 else 'REJECT'

def dev_read(items_path,root,out,only_set,manifest,settings=None,stub=False):
    if only_set=='dev-S1':raise ValueError('MISSING: authorized dev-S1 frame manifest; diagnostic only, never pooled into a decision')
    items=G.items(items_path,only_set);man=G.manifest(manifest)
    G.output(out);root=G.scratch(root)
    registration=G.consume(manifest,settings,stub)
    cache={};inputs={str(items_path):G.sha(items_path),str(manifest):G.sha(manifest),str(G.ledger(stub)):G.sha(G.ledger(stub)),**G.pins()}
    for c in man['captures']:
        t,h=G.validate_done(root,c,manifest,settings,stub);cache[c['canonical']]=t;inputs.update(h)
    est={};detail={};cats=collections.defaultdict(list)
    for x in items:
        parts=[]
        for cat in x['categories']:
            count,slot,per=tool_count(cache[x['scene']],cat)
            parts.append(dict(category=cat,count=count,best_slot=slot,per_slot=per))
        est[x['id']]=sum(p['count'] for p in parts);detail[x['id']]=parts
        for p in parts:cats[p['category']].append(dict(item_id=x['id'],category_count=p['count'],item_truth=x['truth'],item_tool=est[x['id']],single_category=len(parts)==1))
    groups=summarize(items,est)
    category_errors={cat:dict(items=len(xs),tool_zero=sum(x['category_count']==0 for x in xs),item_under=sum(x['item_tool']<x['item_truth'] for x in xs),item_over=sum(x['item_tool']>x['item_truth'] for x in xs),single_category_items=sum(x['single_category'] for x in xs),rows=xs) for cat,xs in sorted(cats.items())}
    result=dict(schema='count-score-v2',stub=stub,only_set=only_set,coverage=dict(items=len(items),with_teacher=len(items),missing_scenes=[]),groups=groups,verdict_primary='STUB_ONLY' if stub else verdict(groups),training_decision=G.config()['training_decision'],per_item={i:dict(tool=est[i],parts=detail[i]) for i in est},category_errors=category_errors,category_error_note='Under/over compares the item total with item truth. Multi-category items do not supply per-category truth.',inputs_sha256=inputs)
    G.write(out,result);G.write(Path(out).with_name(Path(out).stem+'_CATEGORY_ERRORS.json'),dict(stub=stub,categories=category_errors,inputs_sha256=inputs))
    print('coverage',len(items),'/',len(items),'verdict',result['verdict_primary'])

def k1(labels,teacher,captures_meta=None):
    # Explicit diagnostic reproduction only; no configuration writes.
    keep=None if not captures_meta else {c['capture'] for c in G.read(captures_meta)['captures']}
    sc=collections.defaultdict(list)
    for p in sorted(Path(labels).glob('*.labels.json.gz')):
        with gzip.open(p,'rt') as f:lab=json.load(f)
        if keep is not None and lab['canonical'] not in keep:continue
        with gzip.open(Path(teacher)/p.name[:-len('.labels.json.gz')]/'teacher.json.gz','rt') as f:t=json.load(f)
        for name,role in lab['roles'].items():
            if role!='gt':continue
            vis=set().union(*(set(lab['frames'][str(k)].get(name,{}).get('gt_visible',[])) for k in range(32)))
            if vis:sc[str(len(vis)) if len(vis)<=4 else '5+'].append(mra(tool_count(t,name)[0],len(vis)))
    print('K1 diagnostic', {b:dict(n=len(v),MRA=100*float(np.mean(v))) for b,v in sc.items()})

def selftest(items_path):
    assert mra(11,10)==.9 and mra(23,20)==.8 and mra(5,5)==1
    assert mra(None,5)==0 and mra(float('nan'),5)==0
    # Golden values come from N's pinned source, including adjacent floating-point values.
    comparisons=0
    for case in G.read(G.HERE/'MRA_BOUNDARIES.json')['cases']:
        assert mra(case['pred'],case['truth'])==case['expected'],case
        comparisons+=1
    rows=[*G.items(items_path,'R0-dev'),*G.items(items_path,'dev-S1')];mismatches=[];n=0
    for x in rows:
        for arm,d in x['direct'].items():
            n+=1
            if abs(mra(d['pred'],x['truth'])-d['score'])>1e-12:mismatches.append((x['id'],arm))
    assert n==1605 and not mismatches,(n,mismatches)
    r=dict(joint=.35,nms=True,iou=.5,contain=.8,stride=2,kind='max')
    mask={'size':[4,4],'counts':[0,16]}
    assert frame_count([dict(joint_score=.8,mask=mask),dict(joint_score=.7,mask=mask)],r)==1
    r['nms']=False
    assert frame_count([dict(joint_score=.8,mask=mask),dict(joint_score=.7,mask=mask)],r)==2
    assert spearman([1,2,3],[1,2,3])==1
    refs={s:{arm:100*sum(mra(x['direct'][arm]['pred'],x['truth']) for x in rows if x['set']==s and x['truth']>=5)/sum(x['set']==s and x['truth']>=5 for x in rows) for arm in ('S1_544','R1_100','R1_200')} for s in ('R0-dev','dev-S1')}
    G.write(G.WORK/'out/METRIC_TEST.json',dict(stored_scores=n,mismatches=mismatches,threshold_boundary_cases=comparisons,recomputed_references=refs,inputs_sha256={str(items_path):G.sha(items_path),**G.pins()}))
    print('selftest OK;',n,'stored scores;',comparisons,'boundary cases;',json.dumps(refs))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--selftest',action='store_true');ap.add_argument('--items');ap.add_argument('--teacher');ap.add_argument('--out');ap.add_argument('--manifest');ap.add_argument('--settings');ap.add_argument('--stub',action='store_true')
    ap.add_argument('--k1',nargs=2);ap.add_argument('--captures');ap.add_argument('--set',choices=['R0-dev','dev-S1'],default='R0-dev')
    a=ap.parse_args()
    if a.selftest:selftest(a.items)
    elif a.k1:k1(*a.k1,a.captures)
    else:dev_read(a.items,a.teacher,a.out,a.set,a.manifest,a.settings,a.stub)
