import collections
import json
import math
import sys
from pathlib import Path
import numpy as np
import torch
from provenance import sha256, digest, write_json, receipt

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'out'))
import room_gate as gate
O=ROOT.parent
RULES_PATH=ROOT/'work/RULES.json'
ARMS={
 'A1':('qwen_vit',(480,640)), 'A2':('qwen_vit',(768,1024)),
 'A3':('vc_vit',(768,1024)), 'A4':('g3t',(392,518)),
 'A5':('cradio_v4_so400m',(768,1024)), 'A6':('dinov3_vitl16',(768,1024)),
 'A7':('sam3_pe',(1008,1008)), 'A8':('paired',(768,1024)),
 'D2':('dinov2_vitl14_reg',(392,518))}


def rules():
    value=json.loads(RULES_PATH.read_text())
    expected=RULES_PATH.with_suffix('.sha256').read_text().split()[0]
    if sha256(RULES_PATH)!=expected: raise ValueError('Frozen RULES pin differs')
    return value


def normalize_name(name):
    # Use exactly SAM 3's published normalization, from its local helper.
    import importlib.util
    if not hasattr(normalize_name,'fn'):
        p=O/'ttower/work/sam3/common.py'
        spec=importlib.util.spec_from_file_location('own_sam_common',p)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        normalize_name.fn=mod.phrase
    return normalize_name.fn(name)


def read_tuning_metadata(path):
    """Project a mixed metadata file onto tuning before any label/image use."""
    gate.guard_path(path)
    permitted=set(gate.authority()['tuning_scenes'])
    result=[]
    with Path(path).open() as f:
        for line in f:
            row=json.loads(line)
            if row['scene'] not in permitted: continue
            gate.check_row(row,'tuning')
            result.append(row)
    return result


def candidate_inputs():
    cp=O/'verify_kit/out/e1_k5_candidates.jsonl'
    lp=O/'verify_kit/out/e1_k5_tuning_labels.jsonl'
    pp=O/'label_ops/out/p2/p2_identity_labels.jsonl'
    groups=read_tuning_metadata(cp)
    labels={r['object_id']:r for r in read_tuning_metadata(lp)}
    fits={r['object_id']:r for r in read_tuning_metadata(pp)}
    if len(groups)!=221 or sum(len(g['candidates']) for g in groups)!=1105:
        raise ValueError('Tuning candidate cohort differs from frozen 221/1105')
    if {g['object_id'] for g in groups}!=set(labels) or not set(labels)<=set(fits):
        raise ValueError('Incomplete tuning label joins')
    return groups,labels,fits,dict(candidates=sha256(cp),labels=sha256(lp),identity=sha256(pp))


def candidate_truth(group,label,fitting):
    good=[];consistent=[];strict=[]
    indices=set(fitting.get('same_object',[])+fitting.get('also_fits',[]))
    choice=fitting.get('choice',0)
    if isinstance(choice,int) and choice>0: indices.add(choice)
    for i,c in enumerate(group['candidates'],1):
        y=label['candidates'][c['candidate_id']]
        good.append(bool(y['on_target']))
        strict.append(bool(y['strict_on_target']))
        consistent.append(bool(y['on_target']) or i in indices)
    return np.array(good),np.array(consistent),np.array(strict)


def candidate_phrase(group):
    phrases={c['mask_ref']['phrase'] for c in group['candidates']}
    if len(phrases)!=1: raise ValueError('Candidate phrases disagree')
    phrase=phrases.pop()
    if normalize_name(phrase)!=phrase: raise ValueError('Candidate phrase must be normalized')
    return phrase


def mean_ci(values,baseline=None,rooms=None):
    x=np.asarray(values,dtype=np.float64)
    if x.ndim!=1 or len(x)==0 or not np.isfinite(x).all(): raise ValueError('Finite object values required')
    if baseline is not None:
        b=np.asarray(baseline,dtype=np.float64)
        if b.shape!=x.shape: raise ValueError('Paired arrays differ')
        x=x-b
    if rooms is None or len(rooms)!=len(x): raise ValueError('One room ID per paired object required')
    return object_bootstrap([dict(room=r,value=float(v)) for r,v in zip(rooms,x)],
                            lambda rows:float(np.mean([r['value'] for r in rows])))


def auroc(labels,scores):
    labels=np.asarray(labels,dtype=bool);scores=np.asarray(scores,dtype=float)
    n=int(labels.sum());m=len(labels)-n
    if n==0 or m==0:return None
    order=np.argsort(scores,kind='stable');ranks=np.empty(len(scores),float)
    start=0
    while start<len(scores):
        end=start+1
        while end<len(scores) and scores[order[end]]==scores[order[start]]:end+=1
        ranks[order[start:end]]=(start+end-1)/2+1;start=end
    return float((ranks[labels].sum()-n*(n+1)/2)/(n*m))


def object_bootstrap(records,metric):
    """Resample rooms, keeping every object and observation in the sampled room."""
    cfg=rules()['bootstrap'];rng=np.random.default_rng(cfg['seed'])
    clusters=collections.defaultdict(list)
    for r in records:
        room=r.get('room')
        if room is None:
            scene=r.get('scene') or r.get('object_id','').split('::')[0]
            if not scene: raise ValueError('Bootstrap record lacks a room')
            room=gate.room(*scene.split('/'))
        clusters[room].append(r)
    keys=sorted(clusters)
    if not keys: raise ValueError('Bootstrap needs nonempty room clusters')
    value=metric(records)
    samples=[]
    for _ in range(cfg['draws']):
        selected=[r for i in rng.integers(0,len(keys),size=len(keys)) for r in clusters[keys[i]]]
        v=metric(selected)
        if v is not None and math.isfinite(v):samples.append(v)
    return dict(value=value,lo=float(np.quantile(samples,.025)) if samples else None,
                hi=float(np.quantile(samples,.975)) if samples else None,n=len(records),rooms=len(keys),unit='room',valid_draws=len(samples))


def seed_all():
    torch.manual_seed(rules()['seed']);np.random.seed(rules()['seed']);torch.set_num_threads(4)


def admit_shard(path, purpose):
    gate.guard_path(path,purpose)
    manifest=json.loads(Path(str(path)+'.json').read_text())
    gate.check_row(manifest,purpose)
    if manifest['rules_sha256']!=sha256(RULES_PATH) or manifest['sha256']!=sha256(path):
        raise ValueError('Feature shard provenance mismatch')
    obj=torch.load(path,map_location='cpu',weights_only=True)
    for row in obj['records']:gate.check_row(row,purpose)
    return obj,manifest


def output_metrics(path,value,inputs,config):
    value['rules_sha256']=sha256(RULES_PATH)
    value['provenance']=receipt(inputs,sorted((ROOT/'work').rglob('*.py'))+[ROOT/'out/room_gate.py'],config)
    write_json(path,value)
