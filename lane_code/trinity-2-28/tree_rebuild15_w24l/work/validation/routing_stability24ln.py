"""Measure native routing receipt stability with tiny retained CPU inputs."""
import gzip,json,os,sqlite3,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
J=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(J/'work/tree_r1'))
from student_pilot import s1_pool, s1_routing, carrier_c1_routing as R
from student_pilot.p3_provenance import digest,encoded,file_pin,load,write
area=J/'work/validation/routing24ln'

def mocks():
    from contextlib import ExitStack
    stack=ExitStack()
    stack.enter_context(patch('student_pilot.ground_rows.validate',side_effect=R.check_row))
    stack.enter_context(patch('student_pilot.carrier_c1_run.processor_for_receipt',
        return_value=SimpleNamespace(_routing_tokens={'ids':[1,2,3]})))
    stack.enter_context(patch.object(R,'suffix_tokens',side_effect=lambda p,r,t,s: ([ord(c) for c in t],[],[])))
    return stack

def setup():
    area.mkdir()
    inputs=area/'inputs';inputs.mkdir()
    def put(name,value):
        write(inputs/name,value);return file_pin(inputs/name)
    def zipped(name,value):
        (inputs/name).write_bytes(gzip.compress(value.encode(),mtime=0));return file_pin(inputs/name)
    dev=put('dev.json',dict(schema='dev_s1_withhold_v1',canonical={},aliases={},
        natives=['d1/held_dev'],rooms=['d1/held_dev'],physical_groups=['scannet/held_dev']))
    bench=put('bench.json',dict(schema='benchmark_scene_exclusions_v1',scenes=['d1/held_eval'],
        physical_groups=[],rung1_tokens=[],other_corpora={}))
    (inputs/'empty.tsv').write_text('');ep=file_pin(inputs/'empty.tsv')
    exclusions={n:dict(list=ep['path'],list_sha256=ep['sha256'],rows=0) for n in ('dev_s1','eval_rooms','room_release_gate')}
    exclusions['dev_s1'].update(withhold=dev['path'],withhold_sha256=dev['sha256'])
    exclusions['eval_rooms'].update(v2=bench['path'],v2_sha256=bench['sha256'])
    indices=list(range(32))
    events=[dict(kind='plan',text='Measure the camera displacement.'),
        dict(kind='tool_call',token='<move from=1 to=25>',call_id='move'),
        dict(kind='tool_response',text='dx = -0.21 m, dy = +0.28 m, dz = -0.07 m, distance = 0.35 m',call_id='move'),
        dict(kind='canonical_text',text='\nThe printed distance is 0.35 m.')]
    target,spans=R.render(events,'<answer>0.35</answer>')
    row=dict(qid='tiny-program',dataset='d1',scene='clean',schema='derivgen-row-v2',
        form='spec-v3.8-calculator-v2',infrastructure_only=False,question_type='camera_displacement',
        events=events,answer='<answer>0.35</answer>',gt_answer='0.35',target=target,tool_output_spans=spans,
        question='How far did the camera move?',options=[],
        student_input=dict(fps=10),provenance=dict(canonical='scannet/clean',alias='d1/clean',
        source_row_sha256=digest('tiny source'),frame_indices=indices))
    rowpin=zipped('rows.gz',encoded(row)+'\n')
    manifest=put('manifest.json',dict(schema='dose-pool-s1-manifest-v2',exclusions=exclusions,
        sets=[dict(name='PROGRAM',status='final',files={'packed':dict(rowpin,rows=1)})]))
    with mocks():s1_pool.prepare(manifest,inputs/'pool',tokenizer=None)
    selection=file_pin(inputs/'pool/receipt.json')
    assert load(pinned_path:=selection['path'])['sources']['PROGRAM']['status']=='ELIGIBLE'
    frame_map=[]
    for i in indices:
        h=digest(['frame',i]);frame_map.append(dict(d='d1',s='clean',i=i,sha256=h,path='/data2/k6tk/'+h[:2]+'/'+h+'.png'))
    frame=zipped('frames.gz',''.join(encoded(x)+'\n' for x in frame_map))
    frame_plan=zipped('frame_plan.gz',encoded(dict(v={'clean':dict(g='d1',raw_n=32)})))
    division=put('division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,
        train_scenes=['d1/clean'],heldout_scenes=['d1/held_dev','d1/held_eval']))
    db=inputs/'legacy.sqlite';conn=sqlite3.connect(db);conn.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)');conn.commit();conn.close()
    legacy=put('legacy.json',dict(count=0,types={},database=file_pin(db),division=division,scene_role='train'))
    tokenizer=put('model/tokenizer.json',{})
    model=put('model.json',dict(kind='base',root=str(inputs/'model'),files={'tokenizer.json':tokenizer['sha256']}))
    cfg=dict(contract_epoch=False,s1_routing=dict(schema='s1-routing-inputs-v1',selection=selection,
        frame_map=frame,frame_plan=frame_plan),streams=dict(routing=legacy),recipe={},
        route_table={'camera_displacement':'route'},dev_scene_exclusions=dev,benchmark_scene_exclusions=bench,remove_files=[])
    write(area/'request.json',dict(cfg=cfg,division=division,model=model))

def run(label,rootname):
    req=load(area/'request.json');root=area/rootname;root.mkdir()
    with mocks():receipt=s1_routing.build(req['cfg'],root/'selection',req['division'],req['model'])
    assert receipt['count']==1
    write(area/(label+'.json'),dict(pid=os.getpid(),root=str(root),digest=digest(receipt),receipt=receipt))
    root.rename(area/(label+'_retained'))

if sys.argv[1]=='setup':setup()
else:run(*sys.argv[1:])
