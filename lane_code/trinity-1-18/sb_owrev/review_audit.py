"""CPU review; writes evidence only in this review workspace."""
import hashlib, json, random, sys, tarfile, io, math
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

W=Path(__file__).resolve().parent
K=W/'review/kit'; B=W/'review/out/pkg/b200'; S=B/'src'
O=Path('/scratch/jjyeung/orch_n30/sb_ownread')
A=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3/A4')
inputs={}
def raw(p):
    p=Path(p); b=p.read_bytes();inputs[str(p)]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
def rows(p):return [json.loads(l) for l in raw(p).splitlines() if l.strip()]
def unpack(b):
    with tarfile.open(fileobj=io.BytesIO(b)) as t:return {m.name:t.extractfile(m).read() for m in t if m.isfile()}
def boot(values):
    groups=defaultdict(list)
    for room,v in values:groups[room].append(v)
    names=sorted(groups); totals=[math.fsum(groups[k]) for k in names]; counts=[len(groups[k]) for k in names]
    rng=random.Random(17); samples=[]
    for _ in range(10000):
        indices=rng.choices(range(len(names)),k=len(names))
        samples.append(sum(totals[i] for i in indices)/sum(counts[i] for i in indices))
    samples.sort()
    def quantile(q):
        x=q*(len(samples)-1); lo=int(x);return samples[lo]+(x-lo)*(samples[min(lo+1,len(samples)-1)]-samples[lo])
    return dict(value=sum(totals)/sum(counts),ci95=[quantile(.025),quantile(.975)],ci9929=[quantile(.00355),quantile(.99645)],n=sum(counts),rooms=len(names))

result={}
for p in (Path(__file__),K/'ownread.py',K/'build_ownread.py',K/'tests/check_build.py',K/'tests/cpu_proof.py',K/'tests/test_kit.py',K/'ref/REFS.json',K/'vendor/score_r5.py',K/'time_estimate.py',K/'TIME_ESTIMATE.json'):
    raw(p)
tarraw=raw(O/'out/sb_ownread_kit.tar'); side=raw(O/'out/sb_ownread_kit.tar.sha256').decode().split()[0]
assert hashlib.sha256(tarraw).hexdigest()==side
d=unpack(raw(B/'1.tgz')); a=unpack(raw(A/'1.tgz')); p=unpack(d['0.tgz']); old=unpack(a['0.tgz'])
assert all(raw(B/'package'/n)==v for n,v in d.items())
assert all(raw(S/n)==v for n,v in p.items())
for name,h in json.loads(d['PACKAGE.json'])['files'].items():assert hashlib.sha256(d[name]).hexdigest()==h
cfg=json.loads(p['9.json'])
for name,pin in cfg['payload_pins'].items():assert pin==dict(bytes=len(p[name]),sha256=hashlib.sha256(p[name]).hexdigest())
assert raw(W/'work/rebuilt/1.tgz')==raw(B/'1.tgz')
assert raw(O/'out/pkg/b200/1.tgz')==raw(B/'1.tgz')
assert raw(O/'out/OPERATOR_DIFF_VS_A4.patch')==raw(K/'OPERATOR_DIFF_VS_A4.patch')
archive=unpack(tarraw)
assert all(raw(O/n)==b for n,b in archive.items() if n.startswith('kit/'))
result['seal']=dict(kit_sha256=side,delivery_sha256=inputs[str(B/'1.tgz')],delivery_members=len(d),payload_members=len(p),changed_delivery=sorted(n for n in d if d[n]!=a[n]),changed_payload=sorted(n for n in p if p[n]!=old[n]),payload_pins=len(cfg['payload_pins']),rebuild_identical=True,tar_kit_equals_loose_kit=True)

manifest=read(S/'items/devs1_routed.json'); items={r['id']:r for r in manifest['items']}
plan=read(B/'READ_PLAN.json'); selected=plan['item_ids_in_execution_order']
assert len(selected)==len(set(selected))==450
assert all(k.startswith('devs1cam-') for k in selected)
assert all(items[k]['label_authority']=='native_camera_gt' for k in selected)
assert len(set(selected)-set(items))==0
result['scope']=dict(count=len(selected),types=dict(Counter(items[k]['question_type'] for k in selected)),prefixes=sorted({k.split('-')[0] for k in selected}),label_authorities=sorted({items[k]['label_authority'] for k in selected}),item_order_matches_a4=plan['item_order_matches_a4_camera_read'])

sys.path[:0]=[str(S/'tree'),str(S/'b'),str(S),str(K)]
from evalpath.run import score_item
for q in (S/'tree/evalpath/run.py',S/'tree/evalpath/official.py',S/'h1eval/scorers.py',S/'b/e2e_reader/parity.py'):
    raw(q)
root=W/'work/proof/ret_strict'; tables={'own':{},'tower':{}}
for f in sorted((root/'metadata/reads/0/metadata/journals').glob('*/*/items.jsonl')):
    for r in rows(f):
        assert r['id'] not in tables[r['arm']]
        tables[r['arm']][r['id']]=r
saved=read(W/'work/proof/score_strict/ownread.json')
metrics={}; mismatch=0
for kind in ('camera_displacement','camera_movement_direction','camera_rotation'):
    keys=[k for k in items if items[k]['question_type']==kind]
    values={a:{} for a in tables}
    for arm,rs in tables.items():
        for k in keys:
            r=rs[k];o=r['output'];task=items[k]
            # Recompute the reader's answer score from text and the fixed label.
            import re
            score=score_item({**task,'ground_truth':task['answer']},o)
            value=0.0 if o.get('strict_no_answer') or not re.search(r'</think\s*>',o['text'],re.I) or score['parse_failed'] or o['finish']=='max_calls' else score['score']
            mismatch+=int(abs(value-o['scores']['answer'])>1e-12)
            values[arm][k]=value
    gap=boot([(items[k]['room_key'],100*(values['own'][k]-values['tower'][k])) for k in keys])
    own=100*sum(values['own'].values())/len(keys); tower=100*sum(values['tower'].values())/len(keys)
    v=saved['types'][kind]
    assert abs(own-v['own'])<1e-10 and abs(tower-v['tower'])<1e-10
    assert np.allclose(gap['ci95'],v['own_minus_tower']['ci95'],rtol=0,atol=1e-10)
    assert np.allclose(gap['ci9929'],v['own_minus_tower']['ci9929'],rtol=0,atol=1e-10)
    metrics[kind]=dict(own=own,tower=tower,gap=gap,point=gap['value']>=-5,interval=gap['ci95'][0]>-5)
result['synthetic']=dict(metrics=metrics,answer_score_mismatches=mismatch,bootstrap_reimplementation_matches=True)
assert mismatch==0

# Derive time independently from the measured returns.
b1=A.parent/'bases/b1/work/ret'; h=O/'work/h10own_170631'
alloc=read(A/'ret/metadata/ALLOCATION.json'); steps=rows(A/'ret/metadata/reads/0/STEPS.jsonl')
staging=min(r['utc'] for r in steps if r['event']=='start')-(alloc['end']-18000)
t200=sum(r['seconds'] for t in range(3) for r in rows(A/f'ret/metadata/reads/0/metadata/journals/{t}/0/items.jsonl'))
t544=sum(r['seconds'] for t in range(3) for r in rows(b1/f'metadata/reads/0/metadata/journals/{t}/0/items.jsonl'))
load=max(l['load_s'] for r in rows(A/'ret/metadata/reads/0/metadata/journals/3/0/timings.jsonl') for l in r['loads'])
hsteps=rows(h/'STEPS.jsonl');own=0;overheads=[]
for t in range(3):
    rr=rows(h/f'metadata/journals/{t}/0/items.jsonl')
    own+=sum(r['seconds'] for r in rr if r['mode']=='none')
    overheads.append(next(r['utc'] for r in hsteps if r['event']=='exit' and r['type']==t)-next(r['utc'] for r in hsteps if r['event']=='start' and r['type']==t)-sum(r['seconds'] for r in rr))
estimate=staging+3*(max(overheads)+load)+max(t200,t544)+own+120
upper=estimate+.5*(max(t200,t544)+own)
result['timing']=dict(staging=staging,tower200=t200,tower544=t544,own544=own,tower_load=load,own_overheads=overheads,estimate_seconds=estimate,estimate_hours=estimate/3600,decode_x1_5_hours=upper/3600)
assert round(estimate)==read(K/'TIME_ESTIMATE.json')['estimated_seconds']

# Check the H1-0 scale and modes directly against its available source/return.
hp=Path('/scratch/jjyeung/orch_n30/h10_stage/work/k330/kit/h1eval/perception.py')
hist=raw(hp).decode(); now=raw(S/'h1eval/perception.py').decode()
assert "built={'scale':1." in hist and "built={'scale':1." in now
env=read(h/'metadata/journals/0/0/environment.json')
result['own_rule']=dict(historical_source=str(hp),scale_one_in_both=True,historical_modes=env['binding']['modes'],current_modes=plan['read_settings'][0]['modes'])
result['input_sha256']=inputs
(W/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
for k,v in result.items():
    if k!='input_sha256':print(k,json.dumps(v,sort_keys=True))
