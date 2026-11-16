"""Dev-only route freezing and strict replay of an immutable per-type policy."""
from collections import defaultdict
import json
from pathlib import Path
import numpy as np
from evalpath.items import digest,pinned,sha256,index_rows
from scoring import score_item,benchmark_summary

CP1_SHA='c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67'
DEV_SHA='04b0e301a28d7ef36c5b02a11eaea1e46d2751963447f62fc62f60e80887d9d2'
DEV_TYPES={'object_rel_direction_medium','object_rel_direction_hard','object_abs_distance','object_rel_distance'}
PROTOCOL='cp1-native-heads-frozen-dev-v1'

def read_jsonl(pin):
    return [json.loads(s) for s in pinned(pin).read_text().splitlines() if s.strip()]

def validate_table(table,review=False,dev=False):
    if (table.get('schema')!='dev-route-table-v1' or table.get('dev_sha256')!=DEV_SHA
        or table.get('checkpoint_sha256')!=CP1_SHA or table.get('protocol')!=PROTOCOL
        or table.get('default')!='direct' or table.get('selection')!='scene-bootstrap-lower95-positive'
        or (table.get('review_only') and not review) or (table.get('dev_only') and not dev)):
        raise ValueError('Require frozen dev-only CP1 route table, not an official-set or review policy')
    if table.get('dev_only') and dev:
        return table
    if set(table.get('routes', {})) != DEV_TYPES:
        raise ValueError('Route types must equal pinned dev types')
    for key in ('direct_pin','routed_pin'):
        p=table.get(key,{})
        if not p.get('path') or len(p.get('sha256',''))!=64:
            raise ValueError('Route table requires direct_pin and routed_pin')
    for typ,cell in table['routes'].items():
        if cell['action'] not in ('direct','routed') or (cell['action']=='routed') != (cell['ci95'][0]>0):
            raise ValueError('Route action disagrees with frozen dev evidence')
    return table

def action(table,task):
    return table['routes'].get(task['question_type'],{}).get('action','direct')

def freeze(dev_pin,direct_pin,routed_pin):
    if dev_pin['sha256']!=DEV_SHA:raise ValueError('Only the pinned development pool can choose routes')
    dev=read_jsonl(dev_pin)
    if len(dev)!=741:raise ValueError('Require all 741 noReVSI development questions')
    tasks={str(t['id']):dict(t,example_id=str(t['id']),benchmark='devrows') for t in dev}
    arms=[]
    for pin,expected_action in ((direct_pin,'direct'),(routed_pin,'routed')):
        rows=read_jsonl(pin);indexed=index_rows(rows)
        if set(indexed)!=set(tasks) or len(rows)!=741:raise ValueError('Dev generations must cover exactly dev noReVSI 741')
        scores={}
        for key,t in tasks.items():
            r=indexed[key]
            if (r.get('benchmark') not in ('devrows','dev858') or r.get('status')!='complete'
                or r.get('checkpoint_sha256')!=CP1_SHA or r.get('protocol')!=PROTOCOL
                or r.get('route_action')!=expected_action):
                raise ValueError('Dev generation checkpoint/protocol/action mismatch')
            for field in ('question','options','ground_truth','question_type','scene_name'):
                if r.get(field)!=t.get(field):raise ValueError('Dev generation identity mismatch')
            scores[key]=score_item(t,r['raw_generation'],r['output_tokens'],finish=r['finish_reason'])['score']
        arms.append(scores)
    routes={};rng=np.random.default_rng(17)
    for typ in sorted({t['question_type'] for t in tasks.values()}):
        scenes=defaultdict(list)
        for key,t in tasks.items():
            if t['question_type']==typ:scenes[t['scene_name']].append(arms[1][key]-arms[0][key])
        values=list(scenes.values());sums=np.array([sum(v) for v in values]);counts=np.array([len(v) for v in values])
        draws=rng.integers(0,len(values),size=(10000,len(values)))
        lo,hi=np.quantile(sums[draws].sum(1)/counts[draws].sum(1),[.025,.975])
        routes[typ]=dict(action='routed' if lo>0 else 'direct',ci95=[float(lo),float(hi)],
                         delta=float(sums.sum()/counts.sum()),count=int(counts.sum()),scenes=len(values))
    return validate_table(dict(schema='dev-route-table-v1',dev_sha256=DEV_SHA,checkpoint_sha256=CP1_SHA,
        protocol=PROTOCOL,default='direct',selection='scene-bootstrap-lower95-positive',seed=17,
        resamples=10000,direct_pin=direct_pin,routed_pin=routed_pin,routes=routes))

def record(task,decoded,selected,table_sha,media=None):
    """Shared by GPU generation and CPU replay; ignores recorded scores/labels."""
    raw=decoded['text'];tokens=decoded['generated_tokens'];finish=decoded['finish']
    score=score_item(task,raw,tokens,cap=16384,finish='length' if finish in ('max_new_tokens','context_exhaustion','length') else 'stop')
    return dict(task,**score,key=task['benchmark']+':'+task['example_id'],status='complete',
        raw_generation=raw,finish_reason=finish,route_action=selected,route_table_sha256=table_sha,
        checkpoint_sha256=CP1_SHA,protocol=PROTOCOL,layout='duplicate',frames=32,temporal_input_frames=64,
        decode=decoded,media=media)

def replay(tasks,direct,routed,table,table_sha):
    validate_table(table)
    indexes=[]
    for rows in (direct,routed):
        d={}
        for r in rows:
            key=r['benchmark']+':'+r['example_id']
            if key in d:raise ValueError('Duplicate replay generation')
            d[key]=r
        indexes.append(d)
    result=[]
    for task in tasks:
        selected=action(table,task);key=task['benchmark']+':'+task['example_id']
        r=indexes[selected=='routed'].get(key)
        if r is None or r.get('status')!='complete':raise ValueError('Selected generation missing or incomplete: '+key)
        for field in ('question_type','ground_truth','options'):
            if r.get(field)!=task.get(field):raise ValueError('Replay generation identity mismatch')
        if r.get('frames',32)!=32 or r.get('revsi_tier',32)!=32:raise ValueError('Replay frame/tier mismatch')
        decoded=r.get('decode') or dict(text=r['raw_generation'],generated_tokens=r['output_tokens'],finish=r['finish_reason'],calls=[])
        result.append(record(task,decoded,selected,table_sha,r.get('media')))
    return result


def verify_freeze(table, dev_pin, review=False):
    validate_table(table,review=review)
    expected=freeze(dev_pin,table['direct_pin'],table['routed_pin'])
    compared={k:v for k,v in table.items() if not (review and k=='review_only')}
    if expected != compared:
        raise ValueError('Route table differs from recomputed freeze')
    return expected


def route_report(table, tasks, mode='policy'):
    actions={};absent={}
    for t in tasks:
        b=t['benchmark'];typ=t['question_type']
        entry=actions.setdefault(b,{}).setdefault(typ,dict(action=action(table,t) if mode=='policy' else mode,items=0))
        entry['items']+=1
        if typ not in table['routes']:absent.setdefault(b,set()).add(typ)
    return dict(route_actions=actions,absent_types={b:sorted(absent.get(b,set())) for b in actions})


def reuse_direct(tasks, pin, table, request_pin=None):
    rows=read_jsonl(pin);indexed={};bound_cells={}
    if request_pin:
        request=json.loads(pinned(request_pin).read_text())
        for i,cell in enumerate(request['cells']):
            model=request['models'][cell['model']]
            if (model.get('sha256')==CP1_SHA and cell.get('layout')=='duplicate'
                and cell.get('frames',32)==32 and cell.get('decoding','greedy')=='greedy'):
                bound_cells[digest(dict(request=request['binding'],cell=i))]=cell
    for r in rows:
        key=r['benchmark']+':'+str(r['example_id'])
        if key in indexed:raise ValueError('Duplicate direct reuse answer')
        indexed[key]=r
    result={}
    for t in tasks:
        if action(table,t)!='direct':continue
        key=t['benchmark']+':'+t['example_id'];r=indexed.get(key,{})
        bound=bound_cells.get(r.get('binding'),{})
        if bound and t['benchmark'] not in bound['benchmarks']:raise ValueError('Direct request benchmark differs')
        if request_pin and not bound:raise ValueError('Direct request checkpoint/binding/layout differs')
        if (r.get('checkpoint_sha256',CP1_SHA if bound else None)!=CP1_SHA or r.get('status')!='complete'
            or r.get('frames',bound.get('frames',32) if bound else None)!=32 or r.get('layout',bound.get('layout'))!='duplicate'
            or r.get('route_action','direct')!='direct'):
            raise ValueError('Direct reuse checkpoint/status/layout differs or answer missing: '+key)
        for f in ('question','options','ground_truth','question_type','video_sha256','source_frame_indices'):
            if r.get(f)!=t.get(f):raise ValueError('Direct reuse task differs: '+f)
        decoded=r.get('decode') or dict(text=r['raw_generation'],generated_tokens=r['output_tokens'],finish=r['finish_reason'],calls=[])
        result[key]=dict(record(t,decoded,'direct','',r.get('media')),reused_direct=True,
                         direct_source_pin=pin,direct_source_request_pin=request_pin,processed_height_width=r.get('processed_height_width'),
                         visual_tokens_per_frame=r.get('visual_tokens_per_frame'))
    return result


def deadline_reached(cfg, now=None):
    import datetime,time
    until=cfg.get('until')
    if not until:raise ValueError('Missing per-item deadline')
    return (time.time() if now is None else now)>=datetime.datetime.fromisoformat(until.replace('Z','+00:00')).timestamp()
