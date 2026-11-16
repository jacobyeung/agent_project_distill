"""Deterministic id partitions using the measured routed rates and return reserve."""
import math
from collections import defaultdict
from .io import digest
from offkit.report import key
LIMIT=21600
RESERVE=600
RATES={'object_abs_distance':23.768,'room_size_estimation':7.486}

def cost(item):
    kind=item['question_type']
    # Direct decoding lacks a measurement; use the slower measured rate as a proxy.
    return RATES.get(kind,23.768)*(2 if kind in RATES else 1)

# Unmeasured terms are explicit planning allowances, not GPU measurements.
# SAM covers encoding, baseline, dense, aliases and scale/gravity for one scene.
DEFAULT_BUDGETS={'scene_staging_s':30.,'scene_g3t_s':3.8,'scene_sam_s':300.,
                 'loading_s':1200.,'proof_second_load_s':600.,
                 'proof_decode_s':20*23.768,'proof_assets_s':300.,
                 'canary_s':10*23.768}

def plan(items, *, count=None, budgets=None):
    if not items:raise ValueError('empty shard cohort')
    allowance=dict(DEFAULT_BUDGETS)
    if budgets is not None:
        if set(budgets)!=set(allowance):raise ValueError('incomplete timing allowances')
        allowance.update(budgets)
    if any(not math.isfinite(v) or v<0 for v in allowance.values()):
        raise ValueError('invalid timing allowance')
    groups=defaultdict(list)
    for row in items:groups[(row['dataset'],row['scene_name'])].append(row)
    scene=sum(allowance[n] for n in ('scene_staging_s','scene_g3t_s','scene_sam_s'))
    fixed=sum(v for n,v in allowance.items() if not n.startswith('scene_'))
    weights={name:sum(cost(r) for r in rows)+scene for name,rows in groups.items()}
    ordered=sorted(groups,key=lambda name:(-weights[name],name))
    identity=digest([key(r) for r in items])
    def partition(k):
        bins=[[] for _ in range(k)];loads=[0.]*k;scenes=[[] for _ in range(k)]
        for name in ordered:
            slot=min(range(k),key=lambda i:(loads[i],i))
            bins[slot].extend(sorted(groups[name],key=lambda r:digest(key(r))))
            scenes[slot].append(name);loads[slot]+=weights[name]
        result=[]
        for i,rows in enumerate(bins):
            ids=[key(r) for r in rows];ns=len(scenes[i])
            terms={'decode_s':sum(cost(r) for r in rows),
                   **{n:allowance[n]*ns for n in allowance if n.startswith('scene_')},
                   **{n:v for n,v in allowance.items() if not n.startswith('scene_')}}
            estimate=1.25*sum(terms.values())+RESERVE
            result.append({'index':i,'count':k,'ids':ids,'ids_sha256':digest(ids),
                'cohort_sha256':identity,'scenes':[list(v) for v in sorted(scenes[i])],
                'scene_count':ns,'cost_terms':terms,'margin':1.25,'return_reserve_s':RESERVE,
                'estimated_seconds':estimate,'fits_limit':estimate<=LIMIT})
        return result
    minimum=max(1,math.ceil(1.25*sum(weights.values())/(LIMIT-RESERVE-1.25*fixed))) if LIMIT>RESERVE+1.25*fixed else len(groups)+1
    if count is not None:
        if type(count) is not int or count<1 or count>len(groups):raise ValueError('invalid scene shard count')
        candidates=[count]
    else:candidates=range(minimum,len(groups)+1)
    for k in candidates:
        shards=partition(k)
        if all(s['fits_limit'] for s in shards):break
    else:raise ValueError('scene cannot fit six hours with all timing allowances and reserve')
    return {'schema':2,'count':k,'cohort_sha256':identity,'limit_s':LIMIT,'return_reserve_s':RESERVE,
        'measured_rates':RATES,'direct_rate_proxy':23.768,'margin':1.25,
        'planning_allowances':allowance,'partition_unit':'scene',
        'unmeasured':['SAM proposals','staging/model loading','proof','canary','direct decode'],
        'fit_guaranteed':False,'fits_planning_allowances':True,
        'estimated_seconds':sum(s['estimated_seconds'] for s in shards),'shards':shards}

def select(items, shard):
    if not shard:return items
    ids=shard['ids']
    if len(set(ids))!=len(ids) or digest(ids)!=shard['ids_sha256']:
        raise ValueError('shard id identity differs')
    if digest([key(r) for r in items])!=shard['cohort_sha256']:
        raise ValueError('shard cohort differs')
    by_id={key(r):r for r in items}
    if not set(ids)<=by_id.keys():raise ValueError('foreign shard ids')
    return [by_id[k] for k in ids]


def merge_returns(destination, directories):
    """Accept only fetched, authenticated shards; require the exact arm/id union."""
    from .io import load,rows,dump,journal,sha
    from .transport import authenticate
    from .worker import merge
    b=load(destination/'BINDING.json');items=load(destination/'COHORT.json')
    ids=[key(i) for i in items];parts={arm:[] for arm in b['arms']}
    for directory in directories:
        config=load(directory/'CONFIG.json')
        if config['x0']!=b['binding_sha256']:raise ValueError('shard binding differs')
        if config.get('shard',{}).get('cohort_sha256')!=digest(ids):raise ValueError('shard cohort differs')
        authenticate(directory,load(directory/'incoming/EXIT.json'),directory/'incoming/result.tar.gz')
        root=directory/'fetched'
        for arm in parts:
            records=rows(root/(arm+'.jsonl'))
            if not {key(r) for r in records}<=set(config['shard']['ids']):raise ValueError('foreign returned shard id')
            parts[arm].append(records)
    complete={arm:merge(ids,parts[arm]) for arm in parts}
    target=destination/'merged'
    if target.exists():raise ValueError('merge destination exists')
    for arm,records in complete.items():
        for record in records:journal(target/(arm+'.jsonl'),record)
    dump(target/'COMPLETE.json',dict(complete=True,fixture=False,items=len(ids),ids_sha256=digest(ids),
        binding_sha256=b['binding_sha256'],arms=list(complete)))
    from .reporting import report
    return report(b,items,target,destination/'reports')
