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
                      'false_call_rate','repeated_calls','extra_calls','missing_calls','first_call_token_offset','exact'),
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
    # Direct overall rates use baseline items once; type bars retain each type's denominator.
    routed={'camera_displacement','camera_movement_direction','camera_rotation','object_abs_distance'}
    direct={arm:[r for r in rows if r['arm']==arm and r['mode']=='none' and r['type'] not in routed]
            for arm in {r['arm'] for r in rows}}
    for kind, arms in result.items():
        for arm, modes in arms.items():
            for mode, rec in modes.items():
                m=rec['M1']
                val=lambda key: m.get(key,{}).get('value')
                if kind in routed:
                    is_revsi=any(r.get('item_set')=='revsi999' for r in groups[(kind,arm,mode)])
                    rate=.95 if is_revsi and kind=='object_abs_distance' else .98
                    m['bars']=dict(call_rate_min=rate,exact_min=.95,answer_before_first_call_max=.01)
                    m['pass_flags']={k:(val(k) is not None and test(val(k))) for k,test in
                        [('call_rate',lambda v:v>=rate),('exact',lambda v:v>=.95),
                         ('answer_before_first_call',lambda v:v<=.01)]}
                else:
                    overall=bootstrap([(r['room_key'],r['measurements']['M1'].get('false_call_rate',
                        r['measurements']['M1'].get('call_rate',0))) for r in direct[arm]])
                    m['overall_false_call_rate']=overall
                    m['bars']=dict(false_call_rate_max=.05,overall_false_call_rate_max=.02)
                    value=val('false_call_rate')
                    m['pass_flags']=dict(per_type=value is not None and value<=.05,
                        overall=overall['value'] is not None and overall['value']<=.02)
                m['passes_bars']=all(m['pass_flags'].values())
    baseline={(r['id'],r['type'],r['arm']):r for r in rows if r['mode']=='none'}
    differences=defaultdict(list)
    for (identifier,kind,arm), own in baseline.items():
        if arm!='own':continue
        tower=baseline.get((identifier,kind,'tower'))
        if tower is None:continue
        if own['room_key']!=tower['room_key']:raise ValueError('Own/tower paired rooms differ')
        def accuracy(r):
            v=r['measurements'].get('M2',{}).get('task_accuracy')
            return r['measurements'].get('M4',{}).get('score') if v is None else v
        a,b=accuracy(own),accuracy(tower)
        if a is not None and b is not None:differences[kind].append((own['room_key'],100*(a-b)))
    for kind,arms in result.items():
        if 'own' not in arms or 'none' not in arms['own']:continue
        paired=bootstrap(differences[kind])
        m=arms['own']['none']['M2'];m['own_minus_tower']=dict(paired,unit='percentage_points')
        m['bars']=dict(own_minus_tower_lower_bound_gt=-5.)
        m['passes_bars']=paired['ci95'][0]>-5 if paired['ci95'] is not None else None
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
