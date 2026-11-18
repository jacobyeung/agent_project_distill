"""Local census and producer proof; the v7 store is only opened read-only."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import json,sys,os,sqlite3,itertools,subprocess,shutil
L=Path(__file__).resolve().parents[2];B=L/'work/build14';T=L/'work/tree_r1';O=B/'proofs/census'
O.mkdir(parents=True,exist_ok=True)
native_open=Path.open
def proof_open(path,mode='r',*args,**kwargs):
    return native_open(path,mode.replace('x','w') if path.is_relative_to(O) else mode,*args,**kwargs)
Path.open=proof_open
sys.path[:0]=[str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
monitor=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin,write,digest
from student_pilot.carrier_c1_run import Rows
from student_pilot import carrier_c1_routing as routing
from student_pilot.r1_population import produce,family,SLICE_CELLS
from student_pilot.r1_routing import compose,Filters
from student_pilot.r2_adapters import normalize
from student_pilot.r2_intake import intake
from tests.test_r2_build9_recovery import envelope
from tests.test_r2_data_path import fixture
cfg=load(B/'inputs/config.json');card_pin=cfg['r1_training']['mix']
filters=Filters(cfg,cfg['scene_division'])
lane=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/loader_n')
expected=load(lane/'CENSUS.json');plan_expected=load(lane/'ROW_PLAN.json')
sources={k:load(pinned(cfg['r1_training']['row_sources']))[k]['source'] for k in SLICE_CELLS}
for pin in sources.values(): pinned(pin)
batchdir=O/'chunk';batchdir.mkdir(exist_ok=True)
slice_counts={}
catalog=dict(schema='r1-source-catalog-v1',sources={k:dict(source=p,qids=[]) for k,p in sources.items()})
def batches():
    for kind,pin in sources.items():
        counts=Counter();units=Counter()
        with pinned(pin).open() as handle:
            while lines:=list(itertools.islice(handle,200)):
                rows=[]
                for line in lines:
                    raw=json.loads(line);p=raw.get('provenance',{});si=raw.get('student_input',{})
                    catalog['sources'][kind]['qids'].append(raw['qid'])
                    indices=si.get('frame_indices') or raw.get('frame_indices') or p['frame_indices']
                    frames={raw['qid']:dict(fps=si.get('fps') or p.get('fps_source',{}).get('value') or 24.,
                        total_num_frames=indices[-1]+1,frames=[dict(path='/u/'+str(i),sha256='a'*64,source_index=i) for i in indices])}
                    row=normalize(raw,frames);row.update(answer_form='routed',response_heads=['pose','depth'])
                    rows.append(row)
                mp=envelope(batchdir,rows,'routing',kind);manifest=load(mp)
                manifest['extent_receipt']=cfg['extent_receipt'];write(mp,manifest)
                admitted,report=intake(mp)
                counts['read']+=len(rows);counts['intake_admitted']+=len(admitted)
                counts['intake_refused']+=len(report['refusals'])
                # Evidence is summarized once per family, with every batch digest.
                summary=dict(family=kind,source=pin,manifest_sha256=file_pin(mp)['sha256'],
                             admitted=len(admitted),refused=len(report['refusals']))
                write(batchdir/'summary.json',summary)
                yield kind,pin,admitted,file_pin(batchdir/'summary.json')
        slice_counts[kind]=dict(counts)

if '--resume' in sys.argv:
    composed=load(O/'composed/receipt.json')
    slice_counts=load(O/'slice_intake.json')
    con=sqlite3.connect((O/'base.sqlite').as_uri()+'?mode=ro',uri=True)
    camera={family(json.loads(r),'routing'):json.loads(r) for (r,) in con.execute('SELECT row FROM rows')}
    con.close()
else:
    # The fixture uses the native packed-row builder. Its frames and three camera
    # traces are synthetic; the host's catalog selection is not available locally.
    raw=fixture(O,qid='fixture_camera',stream='routing')
    scene=next(s for s in sorted(filters.train) if not filters.reason(dict(qid='fixture',dataset=s.split('/')[0],scene=s.split('/')[1]),'routing'))
    raw['dataset'],raw['scene']=scene.split('/',1)
    raw['provenance']['alias']=scene;raw['provenance']['canonical']='scannet/fixture_clean'
    rgb={k:raw['student_input'][k] for k in ('fps','total_num_frames')}
    rgb['frames']=[dict(p,source_index=i) for p,i in zip(raw['student_input']['frames'],raw['student_input']['frame_indices'])]
    camera={}
    conn=sqlite3.connect(':memory:');conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    for i,kind in enumerate(('camera_displacement','camera_movement_direction','camera_rotation')):
        r=deepcopy(raw);r.update(qid='fixture_'+kind,question_type=kind)
        row=routing.c1_row(r,rgb);camera[kind]=row
        conn.execute('INSERT INTO rows VALUES(?,?,?)',(i,json.dumps(row),'{}'))
    conn.commit();(O/'base.sqlite').write_bytes(conn.serialize());conn.close()
    write(O/'base.json',dict(schema=routing.ROUTING_SCHEMA,stream='routing',database=file_pin(O/'base.sqlite'),
        count=3,division=cfg['scene_division'],heldout_overlap=0,scene_role='train'))
    subprocess.run(['df','-BG','--output=avail','/scratch'],check=True)
    assert shutil.disk_usage('/scratch').free>=85*1024**3
    composed=compose(file_pin(O/'base.json'),sources,batches(),cfg,O/'composed')
    # Batch summaries use one fixed folder; replace ephemeral evidence with immutable aggregate pins.
    write(O/'slice_intake.json',slice_counts)
    write(O/'SOURCE_CATALOG.json',catalog)
    composed['intake_evidence']=[file_pin(O/'slice_intake.json')]
    write(O/'composed/receipt.json',composed)
    print('composed',composed['per_source'],flush=True)
    for k in SLICE_CELLS:
        assert composed['per_source'][k]==sum(expected['streams']['routing_slices'][k]['cells'].values()),k
v=load(pinned(cfg['streams']['vqa']));pinned(v['database'])
reader=Rows(dict(streams={'vqa':dict(database=v['database'],count=v['count']),
    'routing':dict(database=composed['database'],count=composed['count'])},
    r1_training=cfg['r1_training'],extent_receipt=cfg['extent_receipt']),None)
if '--resume' in sys.argv:
    prior=load(O/'CENSUS.json')['vqa'];pinned(prior['database'])
    indices=load(O/'vqa_indices.json');bycell=Counter(prior['eligible_by_cell']);refused=Counter(prior['refused'])
    assert dict(bycell)==expected['streams']['vqa']['eligible_by_cell']
else:
    refused=Counter();indices=[];bycell=Counter()
    for i,encoded in reader.connections['vqa'].execute('SELECT i,row FROM rows ORDER BY i'):
        row=json.loads(encoded);why=filters.reason(row,'vqa')
        if why is None:
            try:reader.row('vqa',i)
            except (ValueError,KeyError,TypeError) as e:why='reader:'+type(e).__name__+':'+str(e)
        if why:refused[why]+=1
        else:indices.append(i);bycell[family(row,'vqa')]+=1
        if (i+1)%50000==0:print('vqa scanned',i+1,flush=True)
    assert dict(bycell)==expected['streams']['vqa']['eligible_by_cell'],(bycell,expected['streams']['vqa'])
reader.indices['vqa']=indices;reader.counts['vqa']=len(indices)
write(O/'vqa_indices.json',indices)
write(O/'CENSUS.json',dict(vqa=dict(read=v['count'],eligible_by_cell=dict(bycell),refused=dict(refused),database=v['database']),
    slices={k:dict(**slice_counts[k],eligible=composed['per_source'][k],source=sources[k]) for k in SLICE_CELLS},
    comparison=file_pin(lane/'CENSUS.json'),standins='Frame pins /u, source ordinals, GUESS 24 FPS when absent; published alias/canonical coverage as in lane census. No RGB loading or independent frame-host coverage proof.'))
# Native reader boundary for unavailable camera/pose/pointing stores. These
# virtual rows exist only for plan arithmetic and are explicitly not a census.
virtual=Rows(dict(streams={},r1_training=cfg['r1_training']),None)
memory=sqlite3.connect(':memory:');memory.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
for s in ('pose','pointing','routing'):virtual.connections[s]=memory
sizes={s:plan_expected['counts'][s] for s in ('pose','pointing')}
cameras={k:plan_expected['counts'][k] for k in camera}
base_cameras=Counter(family(json.loads(r),'routing') for (r,) in reader.connections['routing'].execute('SELECT row FROM rows') if not json.loads(r).get('r1_source'))
class Reader:
    def count(self,s):
        if s in sizes:return sizes[s]
        return reader.count(s)+(sum(cameras.values())-sum(base_cameras.values()) if s=='routing' else 0)
    def row(self,s,i):
        if s=='vqa' or s=='routing' and i<reader.count('routing'):return reader.row(s,i)
        if s in sizes:r=dict(qid='fixture_'+s+'_'+str(i))
        else:
            j=i-reader.count('routing')
            for k,n in cameras.items():
                if j<n-base_cameras[k]:r=deepcopy(camera[k]);r['qid']='fixture_'+k+'_'+str(j);break
                j-=n-base_cameras[k]
        memory.execute('INSERT OR REPLACE INTO rows VALUES(0,?,?)',(json.dumps(r),'{}'))
        return virtual.row(s,0)
write(O/'host_boundary.json',dict(counts=cameras,pose_pointing=sizes,
    source=file_pin(lane/'ROW_PLAN.json'),scope='P admitted counts stand in for unavailable host stores; N scene filtering may lower these counts. Virtual offsets extend the composed fixture; no production binding.'))
binding=produce(Reader(),card_pin,composed['source_membership'],
    [file_pin(O/'CENSUS.json'),file_pin(O/'host_boundary.json'),file_pin(O/'composed/receipt.json')],O/'population')
from student_pilot.r1_mix import validate_binding,plans
card,idx,allocation=validate_binding(binding)
assert allocation==plan_expected['allocation']
owner={(c['stream'],i):c['type'] for c in card['cells'] for i in idx['cells'][c['type']]}
draws=Counter();repeats=Counter();quotas=Counter()
for plan in plans(binding,{s:Reader().count(s) for s in ('pose','vqa','routing','pointing')},1000):
    step=Counter()
    for s,offsets in plan:
        step[s]+=len(offsets)
        for i in offsets:draws[owner[s,i]]+=1;repeats[s,i]+=1
    quotas[json.dumps(step,sort_keys=True)]+=1
assert dict(draws)=={k:v for k,v in allocation['draws'].items() if v}
assert max(repeats.values())<=4
write(O/'PLAN_RUN.json',dict(binding=binding,allocation=allocation,per_step_quotas=dict(quotas),
    draws=dict(draws),largest_repeat=max(repeats.values()),steps=1000,
    facing=load(pinned(binding['population']))['facing'],comparison=file_pin(lane/'ROW_PLAN.json')))
reader.close();memory.close()
monitor.save(O)
(B/'STATUS.md').write_text('# Build 13 status\n\nGO=false. Local census and production functions pass; counts and allocation match the lane. Host camera/pose/pointing inputs remain stand-ins. Evidence: proofs/census/CENSUS.json and PLAN_RUN.json. Kits, mutations and suites remain.\n')
print('PASS census and plan',flush=True)
