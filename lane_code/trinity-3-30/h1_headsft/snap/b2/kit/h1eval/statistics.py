"""Item-weighted means and paired differences with room-cluster uncertainty."""
from collections import defaultdict
import math
import numpy as np

DRAWS = 10000
SEED = 20261115


def bootstrap(values):
    """Resample rooms, keeping every item in each sampled room (ratio estimator)."""
    groups = defaultdict(list)
    for room, value in values:
        if value is not None and math.isfinite(float(value)):
            groups[room].append(float(value))
    if not groups:
        return dict(value=None, ci95=None, n=0, rooms=0)
    groups = [groups[k] for k in sorted(groups)]
    sums = np.array([sum(v) for v in groups]); counts = np.array([len(v) for v in groups])
    rng = np.random.default_rng(SEED); samples = []
    for start in range(0, DRAWS, 200):
        indices = rng.integers(0, len(groups), size=(min(200,DRAWS-start),len(groups)))
        samples.extend((sums[indices].sum(1)/counts[indices].sum(1)).tolist())
    return dict(value=float(sums.sum()/counts.sum()), ci95=np.quantile(samples,[.025,.975]).tolist(),
                n=int(counts.sum()), rooms=len(groups))


def scalar_metrics(row):
    out = {}; measurements = row['measurements']
    for name in ('M1','M3','M4'):
        values = measurements.get(name,{})
        if name == 'M3' and not values.get('eligible'):
            continue
        keys = {'M1':('call_rate','opener_agreement','argument_agreement','order_agreement','answer_before_first_call',
                      'repeated_calls','extra_calls','missing_calls','first_call_token_offset','exact'),
                'M3':('follow','stick','other'), 'M4':('score','parse_failed','hit_token_cap')}[name]
        for key in keys:
            if values.get(key) is not None:
                out[name+'.'+key] = float(values[key])
        if name == 'M1':
            for opener in ('move','turn','pose','depth_at','ground','gap','other'):
                out['M1.opener_'+opener] = float(opener in values.get('openers',[]))
    values = measurements.get('M2',{})
    for key in ('absolute_error_m','relative_error','error_deg','correct'):
        v = [c[key] for c in values.get('calls',[]) if c.get(key) is not None]
        if v: out['M2.'+key] = sum(v)/len(v)
    for key in ('gravity_angle_deg','depth_absrel'):
        if values.get(key) is not None: out['M2.'+key] = values[key]
    for key in ('rotation_error_deg','translation_direction_error_deg','translation_ratio'):
        v = [c[key] for c in values.get('frames',[]) if c.get(key) is not None]
        if v: out['M2.frame_'+key] = sum(v)/len(v)
    v = [x for f in values.get('frames',[]) for x in f.get('fov_error_deg',[])]
    if v: out['M2.frame_fov_error_deg'] = sum(v)/len(v)
    return out


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows: groups[(row['type'],row['arm'],row['mode'])].append(row)
    result = {}
    for (kind,arm,mode), group in sorted(groups.items()):
        metrics = defaultdict(list)
        for row in group:
            for key,value in scalar_metrics(row).items():metrics[key].append((row['room_key'],value))
        record = dict(n=len(group), M1={}, M2={}, M3={}, M4={})
        for name, values in sorted(metrics.items()):
            m,k = name.split('.',1); record[m][k] = bootstrap(values)
        m3 = record['M3']
        m3['eligible'] = sum(r['measurements'].get('M3',{}).get('eligible',False) for r in group)
        m3['bars'] = dict(follow_min=.80,stick_max=.10)
        m3['passes_bars'] = (m3['follow']['value']>=.80 and m3['stick']['value']<=.10) if 'follow' in m3 else None
        result.setdefault(kind,{}).setdefault(arm,{})[mode] = record
    return result


def paired(a,b):
    def keyed(rows):
        result = {}
        for r in rows:
            key = (r['id'],r['type'],r['arm'],r['mode'])
            if key in result:raise ValueError('Duplicate item/arm/mode')
            result[key] = r
        return result
    left,right = keyed(a),keyed(b);groups=defaultdict(lambda:defaultdict(list)); counts=defaultdict(int)
    for key in sorted(left.keys() & right.keys()):
        x,y = left[key],right[key]
        if x['room_key'] != y['room_key']:raise ValueError('Paired room differs')
        group = key[1:];counts[group]+=1
        u,v = scalar_metrics(x),scalar_metrics(y)
        for metric in u.keys() & v.keys():groups[group][metric].append((x['room_key'],v[metric]-u[metric]))
    return [dict(type=k[0],arm=k[1],mode=k[2],shared_items=counts[k],
                 differences={m:bootstrap(v) for m,v in sorted(groups[k].items())}) for k in sorted(counts)]
