import argparse,json,sys,hashlib,re,traceback
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--root',required=True)
parser.add_argument('--config',required=True)
parser.add_argument('--record',required=True)
args=parser.parse_args()
S=Path(args.root).resolve()
MS=S/'sj/orch_cd/evalx/work/milestone'
MAP=[('/scratch/jjyeung','sj'),('/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung','fsw'),('/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap','m/ap')]
def mapped(p):
    p=str(p)
    if p.startswith(str(S)): return Path(p)
    for l,r in MAP:
        if p==l or p.startswith(l+'/'): return S/r/p[len(l)+1:]
    raise ValueError('unmapped '+p)
sys.path[:0]=[str(MS/'native/out2'),str(MS/'orchard_native'),str(MS)]
import common
common.local=lambda path: mapped(Path(path))
import camera_cohort; camera_cohort.local=common.local
import kernels as K, nomdg as N, geometry as G, perception as P, frozen_kit
cfg=json.loads(Path(args.config).read_text())
worker=cfg['worker']; assets=cfg['assets']
results={}
details={}
def step(name,fn):
    try:
        r=fn(); results[name]=dict(passed=True,result=r);print('PASS',name)
        return r
    except Exception as e:
        results[name]=dict(passed=False,error_type=type(e).__name__,error=str(e))
        print('FAIL',name,type(e).__name__,str(e)[:300]); return None
M_GEOM=84
FAMILY_COUNTS=dict(object_abs_distance=150, room_size_estimation=36, camera_displacement=150, camera_movement_direction=150, camera_rotation=150)
from collections import Counter
state={}
def cohort():
    tasks,captures=N.tasks_and_captures(worker['inputs'])
    chosen=[t for t in tasks if N.family(t['question_type']) in N.FAMILIES]
    keys=['devrows:'+t['id'] for t in chosen]
    assert len(captures)==152 and len(keys)==636 and keys==worker['expected_keys'], (len(captures),len(keys))
    names=sorted({t['native'] for t in chosen})
    assert names==worker['geometry_captures'] and len(names)==M_GEOM, len(names)
    assert Counter(N.family(t['question_type']) for t in chosen)==Counter(FAMILY_COUNTS)
    sel=K.select_pilot([dict(key='devrows:'+t['id'],native=t['native'],family=N.family(t['question_type']))
                        for t in chosen],N.FAMILIES,item_keys=worker['pilot_selection']['item_keys'])
    assert sel==worker['pilot_selection'], 'selection differs'
    state.update(chosen=chosen,captures=captures,sel=sel)
    return 'selection equals sealed; captures %s'%sel['captures']
step('worker.cohort (native_worker.py:26-41)',cohort)
def parts():
    p=K.load_parts(dict(nomdg=MS/'native/out2/nomdg.py',geometry=MS/'native/out2/geometry.py'),worker['kernel_source_pins'])
    return sorted(p)
step('kernels.load_parts + partition (kernels.py:117)',parts)
def geosub():
    caps=G.captures(); by={c['native']:c for c in caps}
    req=state['sel']['captures']; allowed=set(worker['geometry_captures'])
    assert set(req)<=allowed<=set(by)
    sel=[c for c in caps if c['native'] in allowed]; assert len(sel)==84
    assert {'d3/41069053','d3/41098149','d3/41254810'}<=allowed
    state['geo']=sel
    return [c['native'] for c in sel]
step('worker.geometry_cohort: all 84 captures and named audit captures',geosub)
def rawtower():
    raw=common.load(common.checked(worker['raw_tower']))
    out=[]
    for c in state['geo']:
        e=raw['captures'][c['native']]; common.checked(e); out.append(c['native'])
    state['raw']=raw
    return dict(schema=raw.get('schema'),weights=raw.get('weights_sha256','')[:8],config=raw.get('config_sha256','')[:8],revision=raw.get('revision'),checked=len(out))
step('geometry.prepare raw pins for all 84 captures',rawtower)
def bynative():
    tasks=common.rows(common.VENDOR/'r3/TASKS.jsonl'); by={}
    for t in tasks: by.setdefault(t['native'],t)
    missing=[c['native'] for c in state['geo'] if c['native'] not in by]
    assert not missing, 'by_native KeyError for '+repr(missing)
    return 'all 84 have an r3 TASKS row'
step('geometry.prepare by_native lookup (geometry.py:113,117)',bynative)
def frames():
    inv=assets['frames_inventory']; fr=worker['frames_root']
    natives={c['native'] for c in state['geo']}|{t['native'] for t in state['chosen'] if 'devrows:'+t['id'] in state['sel']['item_keys']}
    bad=[]
    for n in natives:
        for p in state['captures'][n]['frames']:
            if inv.get(p['path'])!=p['sha256']: bad.append((n,p['path']))
    assert not bad, bad[:3]
    return '%d captures, all frames in sealed frame inventory with equal sha'%len(natives)
step('trainer_row(verify=True) frame pins vs frames_inventory (routed.py:28)',frames)
def masks():
    r=common.load(common.checked(worker['mask_cache']))
    res={}
    res['schema/setting']=(r.get('schema')=='legs1-frozen-mask-cache-v1' and r.get('setting')==P.SETTING)
    res['frozen_kit']=(r.get('frozen_kit')==frozen_kit.identity())
    cur=common.sha(MS/'native/out2/nomdg.py')
    res['producer_sha256']=r.get('producer_sha256')==cur
    res['producer_expected']=cur
    res['producer_actual']=r.get('producer_sha256')
    man=common.load(common.checked(r['manifest']))
    try:
        P.validate_cache_header(man,r['manifest']['sha256'],common.load(common.checked(r['binding'])),common.load(common.checked(r['complete']))); res['cache_header']=True
    except Exception as e: res['cache_header']=repr(e)[:150]
    caps={c['native']:c for c in man['captures']}
    res['capture membership']=(len(caps)==len(man['captures']) and set(r['captures'])==set(caps))
    res['items pin']=(r['items']['sha256']==man.get('items_sha256')); common.checked(r['items'])
    res['sam receipt']=(common.sha(common.checked(r['sam_receipt']))==man['receipt_sha256'])
    dm=common.load(common.checked(r['dense_manifest']))
    res['dense identity']=((dm['experiment']['name'],dm['checkpoint_sha256'],dm['receipt_sha256'])==('dense',P.SAM_SHA,man['receipt_sha256']))
    try:
        kit,_=P.cache_tools(); kit.check_prompt_provenance(man,common.rows(r['items']['path'])); res['prompt provenance']=True
    except Exception as e: res['prompt provenance']=repr(e)[:150]
    class Fake: pass
    m=Fake(); m.receipt=r; m.captures=caps
    m.require_operands=lambda native,names: P.require_phrases(native,names,caps[native]['phrases'])
    refs=common.load(common.checked(worker['inputs']['references']))
    sel=[t for t in state['chosen'] if 'devrows:'+t['id'] in state['sel']['item_keys']]
    try: res['operand_refusals']=N.operand_refusals(sel,refs,m)
    except Exception as e: res['operand_refusals']=repr(e)[:200]
    obj=[t['native'] for t in sel if N.mask_source(t['question_type'])]
    res['mask cache entries for distance items']=[(n, n in r['captures'] and bool(common.checked(r['captures'][n]['cache']))) for n in obj]
    details['masks']=res
    fields=['schema/setting','frozen_kit','producer_sha256','cache_header','capture membership',
            'items pin','sam receipt','dense identity','prompt provenance']
    failed=[name for name in fields if res.get(name) is not True]
    if failed:
        raise ValueError('Mask identities differ: '+','.join(failed))
    if res['operand_refusals'] or not obj or not all(row[1] for row in res['mask cache entries for distance items']):
        raise ValueError('Mask operands or cache entries differ')
    return res
step('perception.Masks.__init__ replica (perception.py:63-89)',masks)
passed=bool(results) and all(row['passed'] for row in results.values())
record=dict(schema='evalx-native-cpu-pin-replica-v1',passed=passed,root=str(S),
    config=dict(path=str(Path(args.config).resolve()),sha256=hashlib.sha256(Path(args.config).read_bytes()).hexdigest()),
    helper=dict(path=__file__,sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),
    checks=results,details=details,cpu_only=True)
with Path(args.record).open('x') as stream:
    json.dump(record,stream,sort_keys=True,indent=2);stream.write('\n')
print('cpu_replica_passed='+str(passed))
if not passed:
    sys.exit(1)
