"""Exercise N's actual prepare closure through its native pointing rebuild on CPU fixtures."""
import hashlib, json, os, resource, sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
TREE=ROOT/'work/final'
sys.path.insert(0,str(TREE))
resource.setrlimit(resource.RLIMIT_AS,(38*1024**3,38*1024**3))
import torch
torch.set_num_threads(16)
torch.set_num_interop_threads(1)
from student_pilot import s1_admission, carrier_c1_data as data, carrier_c1_run as run
from student_pilot import mdg_parent, r1_coverage, pointing_locate as locate
from student_pilot.p3_provenance import file_pin, write, sha256
from tests.test_pointing_locate import fixture, saved

root=ROOT/'work/admission_probe_final'; root.mkdir()
rows,source,division=fixture(root)
original=data.build_stream(source,division,root/'source','pointing')
write(root/'dev.json',dict(schema='dev_s1_withhold_v1',natives=['d1/held'],rooms=[],physical_groups=[],canonical={},aliases={}))
write(root/'benchmark.json',dict(schema='benchmark_scene_exclusions_v1',scenes=['d1/other_held']))
(root/'remove.jsonl').write_text('')
cfg=dict(world_size=4,ground_target_filter=True,training_mode='final',
    dev_scene_exclusions=file_pin(root/'dev.json'),benchmark_scene_exclusions=file_pin(root/'benchmark.json'),
    remove_files=[file_pin(root/'remove.jsonl')],pointing_locate=locate.RULE_PIN,
    streams={name:file_pin(root/'source/receipt.json') for name in ('pose','pointing','vqa','routing')})
write(root/'config.json',cfg)
output=root/'admission';output.mkdir()
native=data.build_stream
captured={}
class PointingPhaseComplete(Exception): pass
def build(*args,**kwargs):
    assert args[3]=='pointing'
    assert kwargs['pointing_locate']==locate.RULE_PIN
    assert kwargs['source_receipt'] is True and kwargs['ground_target_filter'] is True
    captured['receipt']=native(*args,**kwargs)
    captured['forwarded_rule']=kwargs['pointing_locate']
    raise PointingPhaseComplete
with ExitStack() as stack:
    # These stubs isolate the pointing prepare closure; no production admission is asserted.
    stack.enter_context(patch.object(run,'validate',return_value=None))
    stack.enter_context(patch.object(run,'authenticate',return_value='sha256:synthetic-unit-test'))
    stack.enter_context(patch.object(r1_coverage,'deferred',return_value=False))
    stack.enter_context(patch.object(mdg_parent,'bind',return_value={}))
    stack.enter_context(patch.object(data,'build_stream',side_effect=build))
    try:
        s1_admission.admit(file_pin(root/'config.json'),output,[root],threads=16,memory_gib=38,
                           sample_size=1,prepare_only=True)
    except PointingPhaseComplete:
        pass
    else: raise AssertionError('Did not reach the native pointing prepare closure')
receipt=captured['receipt']
locate.assert_store(receipt,locate.RULE_PIN)
assert receipt['count']==3
assert receipt['target_filter']['settings']['shape_filter'] is True
assert receipt['source_scene_exclusions']['sources']['pointing']['seen']==4
for row in saved(receipt):locate.assert_target(row)
inputs={str(p):sha256(p) for p in (Path(__file__),ROOT/'out/SETUP.json',root/'config.json',
    root/'source/receipt.json',root/'source/rows.sqlite',root/'division.json',root/'dev.json',
    root/'benchmark.json',root/'remove.jsonl',root/'masks.npz',root/'rgb.png')}
for mod in tuple(sys.modules.values()):
    p=getattr(mod,'__file__',None)
    if p and Path(p).is_file() and Path(p).is_relative_to(TREE):inputs[p]=sha256(p)
record=dict(command='bash code/run.sh admission_probe',input_sha256=inputs,status='PASS',
    admitted_pointing_rebuild_rows=receipt['count'],forwarded_rule=captured['forwarded_rule'],receipt=receipt,
    scope='Synthetic CPU fixture: actual s1_admission.admit prepare closure, source_receipt reader, mask builder, target filter and scene exclusions.',
    limitations='Stopped via a test sentinel after pointing build. No host admission, parent-model binding, VQA build, training or full N launch was asserted.',
    stubs=['carrier_c1_run.validate','carrier_c1_run.authenticate','r1_coverage.deferred','mdg_parent.bind'])
(ROOT/'out/ADMISSION_PROBE.json').write_text(json.dumps(record,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Stage 4: N\'s actual admission prepare closure forwards the pinned Locate rule into the native pointing builder. Its synthetic receipt-source fixture retains three rows, with native masks, target filtering and scene exclusions checked. The full base CPU suite finished; the new suite is running. Real-mask rebuilding remains MISSING because local pointing masks and RGB assets are not staged.\n')
print('PASS actual admission prepare closure; native pointing rows:',receipt['count'])
