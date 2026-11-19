"""CPU metadata mapping and operator rehearsal; no weights, frames or inference."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
HERE=Path(__file__).resolve().parent
src=HERE/'in/H544/src'
sys.path[:0]=[str(src/'b'),str(src/'tree'),str(src)]
import e2e_reader
assert str(src/"b") in e2e_reader.__file__
from h1eval.items import load_manifest
from h1eval.h10.parity_adapter import map_items
report=json.loads((HERE/'TEST_RESULTS.json').read_text());evidence=Path(report['evidence'])
build=json.loads((evidence/'build/BUILD.json').read_text())['H'];package=Path(build['package'])
w=Path(tempfile.mkdtemp(prefix='runtime-',dir=str(HERE/'validation')))
(w/'items').mkdir();(w/'items/HELDOUT_CAMERA_ITEMS.json').write_bytes((evidence/'build/items.json').read_bytes())
m=load_manifest(w/'items/HELDOUT_CAMERA_ITEMS.json')
settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',perception_memo_modules=['g3t'],perception_memo_verify_ids=[],save_own_depth=False,arm='own_depth',tasks=[str(src/'items/HELDOUT_NATIVE_TASKS.jsonl')],frames_root=str(w/'no_images'))
settings['item_sets']={'heldout_camera_wording':dict(tasks=settings['tasks'])}
mapped,mapping=map_items(m['items'],settings,name=m['name'])
assert len(mapped)==len({i['key'] for i in mapping['items']})==418
full=load_manifest(src/'items/HELDOUT_CAMERA_ITEMS.json');fm,full_mapping=map_items(full['items'],settings,name=full['name'])
by={i['id']:i for i in full_mapping['items']}
assert all(i==by[i['id']] for i in mapping['items'])
sp=importlib.util.spec_from_file_location('operator_hrem',str(package/'a/6.py'));op=importlib.util.module_from_spec(sp);sp.loader.exec_module(op)
(w/'settings.json').write_text(json.dumps(settings))
conf=dict(package=str(w),output=str(w/'rehearsal'),settings=str(w/'settings.json'),plan_sha256='a'*64,inputs_sha256='b'*64,operator_sha256='c'*64,python=sys.executable,export=str(w/'export'),binding=str(w/'binding'),export_pin=str(w/'pin'),device='cpu',prefix=[])
rehearsal=op.rehearsal(conf)
assert rehearsal[0]['expected']==418 and rehearsal[0]['types']==['camera_rotation','camera_movement_direction']
args=rehearsal[0]['args'];assert Path(args[args.index('--items')+1]).read_bytes()==(w/'items/HELDOUT_CAMERA_ITEMS.json').read_bytes()
summary=op.run(conf,100000,['0'],runner=lambda *a,**k:dict(completed=418,complete=True,failure=None),clock=lambda:0)
assert summary['expected']==summary['completed']==418 and summary['complete']
assert op.memory_bound()['fits']
r=dict(passed=True,mapped=418,full_parent_mapping_equal=True,operator_rehearsal=True,synthetic_runner=True,weights_loaded=False,evidence=str(w))
(HERE/'RUNTIME_TEST_RESULTS.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
