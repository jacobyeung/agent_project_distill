"""Independent recomputation of the step-544 direct reads (no offkit, no kit scorer imports)."""
import json, re, sys, numpy as np
from collections import defaultdict
IN='/scratch/jjyeung/orch_n30/b07_offread/in/'
def rows(p): return [json.loads(l) for l in open(p) if l.strip()]
def final(raw):
    c=list(re.finditer(r'</think\s*>',raw,re.I))
    if not c: return ''
    t=re.sub(r'(?:\s*<\|(?:im_end|endoftext)\|>)+\s*$','',raw[c[-1].end():]).strip()
    m=re.findall(r'<answer>(.*?)</answer>',t,re.S)
    if m: return m[-1].strip()
    L=[x.strip() for x in t.splitlines() if x.strip()]
    return re.sub(r'^(?:final\s+answer|answer)\s*:\s*','',L[-1],flags=re.I).strip() if L else ''
def mra(p,g,bench):
    n=int((0.95-0.5)/0.05+2)
    if bench=='revsi':
        import torch; th=np.array(torch.linspace(0.5,0.95,steps=n,dtype=torch.float64).tolist())  # ReVSI official metric
    else: th=np.linspace(0.5,0.95,n)  # lmms-eval vsibench
    if g==0: return 1.0 if p==0 else 0.0
    return float(np.mean(abs(p-g)/g<=1-th))
MCA_V={'object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard','object_rel_distance','route_planning','obj_appearance_order'}
NUM_R={'object_counting_single','object_counting_multiple','object_abs_distance','object_size_estimation','room_size_estimation_single','room_size_estimation_multiple'}
def score(r,bench,m=None):
    a=m['raw_answer'] if m and m.get('forced_close') else final(r['raw_generation']); tok=a.split(' ')[0].rstrip('.').strip()
    num = (r['question_type'] in NUM_R) if bench=='revsi' else (r['question_type'] not in MCA_V)
    if not num: return 1.0 if tok.lower()==str(r['ground_truth']).strip().lower() else 0.0, a
    try: p=float(tok)
    except ValueError: return 0.0, a
    if not np.isfinite(p): return 0.0, a
    return mra(p,float(r['ground_truth']),bench), a
GROUPS={'vsi':{'object_counting':['object_counting'],'object_size_estimation':['object_size_estimation'],'object_rel_distance':['object_rel_distance'],
  'object_rel_direction':['object_rel_direction_easy','object_rel_direction_medium','object_rel_direction_hard'],'route_planning':['route_planning'],'obj_appearance_order':['obj_appearance_order']},
 'revsi':{'object_counting':['object_counting_single','object_counting_multiple'],'object_rel_direction':['object_rel_direction_forward_easy','object_rel_direction_backward_easy','object_rel_direction_forward_hard','object_rel_direction_backward_hard'],
  'object_rel_distance':['object_rel_distance_closest','object_rel_distance_farthest'],'object_size_estimation':['object_size_estimation'],'route_planning':['route_planning']}}
def run(bench,budget,seeds):
    R=rows(IN+f'ret_{bench}/a0/results/0/budget_{budget}.jsonl'); M={m['source_key']:m for m in rows(IN+f'ret_{bench}/a0/results/0/budget_{budget}.meta.jsonl')}
    mism=0; recs=[]
    for r in R:
        s,a=score(r,bench,M[r['key']])
        if r['status']!='complete' or M[r['key']].get('derivation_error'): s=0.0
        if abs(s-r['score'])>1e-12 or a!=r['extracted_answer']: mism+=1
        recs.append((r['question_type'],(r['dataset'],r['scene_name']),s))
    G=GROUPS[bench]; types=[t for ts in G.values() for t in ts]
    scenes=sorted({x[1] for x in recs}); si={s:i for i,s in enumerate(scenes)}; ti={t:i for i,t in enumerate(types)}
    tot=np.zeros((len(scenes),len(types))); cnt=np.zeros_like(tot)
    for t,sc,s in recs: tot[si[sc],ti[t]]+=s; cnt[si[sc],ti[t]]+=1
    pt=tot.sum(0)/cnt.sum(0)
    gp={g:np.mean([pt[ti[t]] for t in ts]) for g,ts in G.items()}
    head=np.mean(list(gp.values()))
    out=dict(bench=bench,budget=budget,items=len(recs),scenes=len(scenes),score_mismatch_vs_stored=mism,headline=round(100*head,4),groups={g:round(100*v,4) for g,v in gp.items()},ci={})
    for seed in seeds:
        w=np.random.default_rng(seed).multinomial(len(scenes),np.full(len(scenes),1/len(scenes)),size=10000)
        sub=(w@tot)/np.where(w@cnt>0,w@cnt,np.nan)
        gd=[np.mean(sub[:,[ti[t] for t in ts]],axis=1) for ts in G.values()]
        hd=np.mean(gd,axis=0); hd=hd[np.isfinite(hd)]
        out['ci'][seed]=[round(100*x,2) for x in np.percentile(hd,[2.5,97.5])]
    return out
for b in ('vsi','revsi'):
    for bud in (2048,4096):
        print(json.dumps(run(b,bud,[544,1,2,3])))
