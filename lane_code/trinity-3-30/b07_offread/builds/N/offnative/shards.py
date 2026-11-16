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

def plan(items, *, count=None):
    scene_cost=3.8*len({(r['dataset'],r['scene_name']) for r in items})
    seconds=sum(cost(r) for r in items)+scene_cost
    k=count or max(1,math.ceil(1.25*seconds/(LIMIT-RESERVE)))
    if k>len(items) or k<1:raise ValueError('invalid shard count')
    groups=defaultdict(list)
    for row in items:groups[row['question_type']].append(row)
    bins=[[] for _ in range(k)];loads=[0.]*k
    for kind,rows in sorted(groups.items(),key=lambda kv:-cost(kv[1][0])):
        for row in sorted(rows,key=lambda r:digest(key(r))):
            slot=min(range(k),key=lambda i:(loads[i],len(bins[i]),i))
            bins[slot].append(key(row));loads[slot]+=cost(row)
    identity=digest([key(r) for r in items])
    return {'schema':1,'count':k,'cohort_sha256':identity,'limit_s':LIMIT,'return_reserve_s':RESERVE,
        'measured_rates':RATES,'direct_rate_proxy':23.768,'margin':1.25,
        'unmeasured':['SAM proposals','staging/model loading','proof','canary'],
        'fit_guaranteed':False,'estimated_seconds':seconds,
        'shards':[{'index':i,'count':k,'ids':ids,'ids_sha256':digest(ids),
                   'cohort_sha256':identity,'estimated_seconds':1.25*(loads[i]+scene_cost/k)}
                  for i,ids in enumerate(bins)]}

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
