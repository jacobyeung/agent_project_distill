"""Isolated probes of the actual reviewed reader; no weight loader runs."""
import inspect
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch

K = Path(__file__).resolve().parents[1]
B = Path('/scratch/jjyeung/orch_n30/b04_e2ehook')
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
from h1eval.h10.launch import reader_factory, run as launch_run, parser as launch_parser
maker = reader_factory(B)
from e2e_reader import parity
from h1eval.h10 import parity_adapter as A
from h1eval.h10.perception_own import perception_factory, LazyStageOne
from h1eval.items import load_manifest, sha
from h1eval.h10.cpu_first_batch import run as cpu_run, parser as cpu_parser
from h1eval.modes import read_counts, DEFAULT_MODES
from h1eval.cli import modes
from parity_kit import common as C
from parity_kit import provenance as P

report = {}
inspect.signature(parity.make_real).bind('export', {}, [], perception_factory=None,
                                       device='cpu', settings={'arm':'own_depth'})
assert Path(inspect.getsourcefile(maker)).resolve() == B/'e2e_reader/parity.py'
report['signature'] = str(inspect.signature(maker))
settings = dict(frames_root='/scratch/jjyeung/devs1_frames')
dev = load_manifest(K/'items/devs1_routed.json')
rev = load_manifest(K/'items/revsi999.json')
mapped, mapping = A.map_items(dev['items'], settings)
assert len(mapped) == 636 and all(r['layout_count'] == 32 for r in mapping['items'])
report['mapping'] = dict(count=len(mapped), sha256=mapping['sha256'],
                         dense_counts={n:sum(r['dense_count']==n for r in mapping['items']) for n in (32,64)})
(OUT/'mapping.json').write_text(json.dumps(mapping, indent=2)+'\n')

def refuses(fn, contains):
    try:fn()
    except (ValueError, KeyError) as error:
        assert contains in str(error), (contains, str(error))
    else:raise AssertionError('Expected refusal: '+contains)

refuses(lambda:A.map_items(rev['items'], settings, name='revsi999'), 'frames not staged')
refuses(lambda:A.map_items([{**dev['items'][0], 'id':'missing'}], settings), 'unmapped')
refuses(lambda:A.map_items([{**dev['items'][0], 'question':'changed'}], settings), 'binding differs')
report['mapping_refusals'] = True
# A staged ReVSI task uses the same exact native metadata contract as dev-S1.
item = rev['items'][0]
reference = mapped[dev['items'][0]['id']]
staged = dict(item, answer=item['ground_truth'], native='d3/'+item['scene'], room=item['room_key'])
rev_tasks=OUT/'rev_tasks.jsonl';rev_tasks.write_text(json.dumps(staged)+'\n')
capture = dict(parity._captures(C.FRAMES)[reference['native']], native=staged['native'])
dense_capture = dict(parity._captures(C.DENSE)[reference['native']], native=staged['native'])
rm, _=A.map_items([item],dict(settings,tasks=[str(rev_tasks)],
    frames_json={'captures':{staged['native']:capture}},
    dense_manifest={'captures':{staged['native']:dense_capture}}),name='revsi999')
assert rm[item['id']]['question']==item['question']
report['revsi_staged_binding'] = True
# Tiny heads exercise the production factory, using b04's keyword invocation.
import numpy as np
import torch
from tests.test_eval import sample_heads
from e2e_reader.grounding import StageOneSocket

def socket(frames, geometry):
    def propose(name):
        mask=np.zeros((16,16),bool)
        mask[3:12,1:6 if name=='chair' else 2]=True
        if name!='chair':mask[3:12,10:15]=True
        return [dict(candidate_id=name,masks={3:mask,8:mask})],torch.tensor([[1.]])
    return StageOneSocket(propose,lambda x:0,(16,16),32)

model=torch.nn.Linear(2,2).eval();model.h10_stage1_socket=socket
from PIL import Image
image=Image.new('RGB',(4,4))
heads=sample_heads()
frame_data=dict(native_frames=[image]*32, anchor_slots=list(range(32)), anchor_indices=list(range(32)))
task=next(t for t in mapped.values() if t['question_type']=='camera_displacement')
p=perception_factory(artifact=NS(), model=model, processor=NS(), device='cpu', item=task,
                     mode={'name':'scale_translation','k':2.})
routes,built=p.lazy(frame_data,NS(heads=heads),{})
assert all(built['finite_heads'].values())
assert np.allclose(built['heads'].pose9[:,:3],heads.pose9[:,:3]*2)
assert routes['move']('<move from=1 to=9>')[1]['perception']=='own'
refuses(lambda:perception_factory(artifact=NS(),model=model,processor=NS(),device='cpu',item=task,
                                   mode={'name':'negate_turn'}), 'does not apply')
report['keywords_modes_finite'] = True
# Ground/gap run the reviewed StageOne factory with components authenticated against the same artifact.
import e2e_reader.stage1 as stage1
import student_pilot.sam3_tower as sam_module
samsettings=dict(sam3=dict(checkpoint_path=str(OUT/'sam.pt'),receipt_path=str(OUT/'sam.json')),
                 selector_head=str(OUT/'selector'))
artifact=NS(files=lambda name:{(OUT/'sam.pt').resolve(),(OUT/'sam.json').resolve()})
plainmodel=NS()
with patch.object(parity,'_head',return_value='selector') as head_loader, \
     patch.object(sam_module,'Sam3Tower',return_value='sam') as sam_loader, \
     patch.object(stage1,'stage1_factory',return_value=lambda frames,geometry:'socket') as stage_loader:
    assert LazyStageOne(artifact,plainmodel,'cpu',samsettings)({},None)=='socket'
    assert LazyStageOne(artifact,plainmodel,'cpu',samsettings)({},None)=='socket'
    assert head_loader.call_count==sam_loader.call_count==1
    assert stage_loader.call_count==2
    assert stage_loader.call_args.args[:2]==('sam','selector')
report['stageone_artifact_cache'] = True
# Actual parity.make_real constructs its generator and calls the kit factory with all five keywords.
export=OUT/'export';export.mkdir();(export/'RESTORE.json').write_text('{"step":544}\n')
artifact_path=OUT/'artifact.json'
artifact_path.write_text(json.dumps(dict(root=str(OUT),name='manifest.json',sha256='fake')))
settings.update(export_dir=str(export),artifact_manifest=str(artifact_path),tree=str(K/'tree'),
                config=str(OUT/'config.json'),arm='own_depth')
(OUT/'config.json').write_text('{}\n')
settings_path=OUT/'settings.json';settings_path.write_text(json.dumps(settings))
loaded=[]
def tiny_load(*args,**kwargs):
    loaded.append(1)
    processor=NS(tokenizer=NS(),_routing_tokens={'ids':{'move':7}})
    return model,processor,dict(config={},export={'frame_layout':'duplicate'})

def bound_no_pixels(item,settings,**kwargs):
    bound=original_bind(item,settings,verify=False)
    bound['frames']['native_frames']=[image]*len(bound['frames']['native_frames'])
    return bound

def tiny_generate(self,item):
    routes,built=self.perception.lazy(item['frames'],NS(heads=heads),{})
    from rows.expected_calls import expected_calls
    from h1eval.scorers import signature
    native=mapped[item['row']['qid']]
    calls=[]
    for call in expected_calls(native['question'],native['question_type']):
        response,info=routes[signature(call)[0]](call)
        calls.append(dict(call=call,response=response,served=True,**info))
    return dict(text='</think><answer>1.00 meters</answer>',finish='eos',calls={'records':calls},
                tokens=[1],seconds=.001,timings={'tiny_s':.001},frames=self.frames)
original_bind=parity.bind_item
with patch.object(parity,'Artifact',return_value=NS(verify=lambda:NS())), \
     patch.object(parity,'load_native',side_effect=tiny_load), \
     patch.object(parity,'install_hook',side_effect=lambda model,hook:hook), \
     patch.object(parity,'CallHook',return_value=NS()), \
     patch.object(parity,'bind_item',side_effect=bound_no_pixels), \
     patch.object(parity,'score',return_value={'answer':0.,'released_answer':0.}), \
     patch.object(parity,'policy',return_value=NS()), \
     patch.object(parity.ParityGenerator,'__call__',tiny_generate):
    args=cpu_parser().parse_args(['--reader-root',str(B),'--settings',str(settings_path),
                                 '--out',str(OUT/'cpu')])
    cpu=cpu_run(args,maker=maker)
    assert cpu['passed'] and len(cpu['items'])==8 and len(loaded)==1
    assert all(r['text']=='</think><answer>1.00 meters</answer>' for r in cpu['items'])
    assert {r['type'] for r in cpu['items']}==set(__import__('h1eval.h10.cpu_first_batch',fromlist=['MODES']).MODES)
    # A shard spans camera and grounded types and exercises mode switching on one loaded model.
    args=launch_parser().parse_args(['--items',str(K/'items/devs1_routed.json'),'--export',str(export),
        '--artifact-manifest',str(artifact_path),'--reader-root',str(B),'--settings',str(settings_path),
        '--out',str(OUT/'launch'),'--arms','own','--device','cpu','--shard','0/150'])
    run=launch_run(args,make_real=maker)
    assert len(loaded)==2
    before=(OUT/'launch/items.jsonl').read_bytes()
    resumed=launch_run(args,make_real=maker)
    assert resumed['added']==0 and len(loaded)==2 and before==(OUT/'launch/items.jsonl').read_bytes()
    recorded=[json.loads(l) for l in before.splitlines()]
    assert all(r['intervention']==r['output']['intervention']['mode'] for r in recorded)
    report['reviewed_launch_resume']=run
report['cpu_eight_reads']=dict(count=len(cpu['items']),passed=cpu['passed'],loads=1)
report['read_counts']={name:read_counts(items,modes(DEFAULT_MODES),tower_reused=True)
                       for name,items in [('devs1',dev['items']),('revsi',rev['items'])]}
# Synthetic parity-load-v2 partitions use the exact published row-binding functions.
chosen=dev['items'][:2]
runtime={'python':'tiny'}
inputs=dict(settings=settings,config=C.pin(settings['config']),frames_json=C.pin(C.FRAMES),
            dense_manifest=C.pin(C.DENSE),request=C.pin(C.REQUEST),tasks=[C.pin(p) for p in C.TASKS],
            runtime_code=[C.pin(p) for folder in ('parity_kit','e2e_reader') for p in sorted((B/folder).glob('*.py'))]
                         +[C.pin(C.C8R/'reader_policy.py')])
base=dict(schema='parity-load-v2',arm='own_depth',device='cuda:0',inputs=inputs,
          settings_sha256=P.digest(settings),runtime_identity=runtime,runtime_identity_sha256=P.digest(runtime),
          restore=A.read(export/'RESTORE.json'),restore_pin=C.pin(export/'RESTORE.json'),
          artifact_manifest=A.artifact_spec(artifact_path))
paths=[]
for i,item in enumerate(chosen):
    task=mapped[item['id']];key=parity.key(task)
    folder=OUT/'tower/gpu_results'/f'own_depth_p{i}';folder.mkdir(parents=True)
    receipt=dict(base,keys=[key],dense_frame_counts={key:32})
    C.write(folder/'LOAD_RECEIPT.json',receipt)
    row=dict(key=key,id=key,question_type=task['question_type'],room=task['room'],stratum=task.get('stratum'),
             text='</think><answer>1.00 meters</answer>',tokens=[1],finish='eos',calls={'records':[]},
             seconds=1.,scores={'answer':1.,'released_answer':None},frames={'layout':'duplicate','count':32},
             **P.row_binding(receipt,C.sha(folder/'LOAD_RECEIPT.json')))
    (folder/'items.jsonl').write_text(json.dumps(row)+'\n');paths.append(folder)

def convert():
    return A.parity_tower_records(OUT/'tower',chosen,mapped,settings=settings,export=export,
                                  artifact=artifact_path,reader_root=B)
converted,pins=convert()
assert len(converted)==2 and all(r['output']['text']=='</think><answer>1.00 meters</answer>' for r in converted)
journal=paths[1]/'items.jsonl';original=journal.read_text()
journal.write_text(original.rstrip());refuses(convert,'Incomplete');journal.write_text(original)
journal.write_text('');refuses(convert,'missing');journal.write_text(original)
row=json.loads(original);row['load_receipt_sha256']='wrong'
journal.write_text(json.dumps(row)+'\n');refuses(convert,'provenance');journal.write_text(original)
original_restore=(export/'RESTORE.json').read_text()
(export/'RESTORE.json').write_text('{"step":543}\n');refuses(convert,'export');(export/'RESTORE.json').write_text(original_restore)
original_artifact=artifact_path.read_text()
artifact_path.write_text(json.dumps(dict(root=str(OUT),name='manifest.json',sha256='changed')))
refuses(convert,'artifact');artifact_path.write_text(original_artifact)
refuses(lambda:A.parity_tower_records(OUT/'tower',chosen,mapped,settings=settings,export=export,
    artifact=artifact_path,reader_root=OUT/'absent'), 'code inventory')
# Duplicate partitions refuse even when each partition has valid provenance.
extra=OUT/'tower/gpu_results/own_depth_p2';extra.mkdir()
(extra/'LOAD_RECEIPT.json').write_text((paths[0]/'LOAD_RECEIPT.json').read_text())
(extra/'items.jsonl').write_text((paths[0]/'items.jsonl').read_text())
refuses(convert,'Duplicate')
report['tower_conversion']=dict(count=len(converted),refusals=['torn','missing','provenance','duplicate','export','artifact','code'])
(OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
