"""Bind the scoring plan to the actual freshly built package; Python 3.6 stdlib."""
import hashlib
import json
import runpy
import sys
import tarfile
from pathlib import Path

def make(package, binding, template):
    p=Path(package)
    public=json.loads((p/'0.json').read_text())
    with tarfile.open(str(p/'0.tgz')) as archive:
        cfg=json.load(archive.extractfile('9.json'))
        items=json.load(archive.extractfile('items/devs1_routed.json'))['items']
    op=runpy.run_path(str(p/'a/6.py'),run_name='read_plan')
    assert op['COUNTS']==(150,150,150,0,0) and op['SCHEDULE']==((0,0),(0,1),(0,2))
    for k,v in cfg['export_binding'].items():
        assert binding[k]==v,k
    ids={i['id'] for i in items if i['question_type'] in cfg['order'][:3]}
    assert len(ids)==450
    plan=json.loads(json.dumps(template))
    plan.update(token=public['token'],plan_sha256=public['plan_sha256'],
        operator_sha256=hashlib.sha256((p/'a/6.py').read_bytes()).hexdigest(),
        expected=[450],read_settings=op['descriptors'](str(p)),sequence=[list(x) for x in op['SCHEDULE']],
        walltime='03:00:00',export_binding={k:binding[k] for k in plan['export_binding']},
        export_identity_seal='PACKAGE.json pins the operator and fill helper; payload 9.json seals the step-600 export binding.',
        operations_file='REPORT_A600C.md',item_sets={'dev-S1':450})
    plan['item_ids_in_execution_order']=[i for i in plan['item_ids_in_execution_order'] if i in ids]
    assert len(plan['item_ids_in_execution_order'])==450
    return plan

if __name__=='__main__':
    package,binding,template,output=sys.argv[1:]
    plan=make(package,json.loads(Path(binding).read_text()),json.loads(Path(template).read_text()))
    Path(output).write_text(json.dumps(plan,indent=2,sort_keys=True)+'\n')
