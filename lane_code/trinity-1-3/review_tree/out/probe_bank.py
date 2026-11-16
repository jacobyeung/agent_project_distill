import json, unittest
from pathlib import Path
from student_pilot import r2_policy as P
from student_pilot.p3_provenance import file_pin, digest, write
from tests.test_r2_policy import evidence, directory, LANE
root = directory(); reg = evidence(root/'e')
prereg = file_pin(LANE/'work/records/design/REFREEZE_PREREGISTRATION_20261115.json')
def bank(items, facts):
    p = root/'bank.json'; p.write_text(json.dumps(items))
    c = dict(schema='r2-bank-catalog-v1', reader_sha256=P.reader_hash(), items={digest(i): facts for i in items})
    cp = root/'cat.json'; cp.write_text(json.dumps(c)); return file_pin(p), file_pin(cp)
out = {}
# 1. MindCube-style items relabelled as development data in the caller's catalog
items = [dict(id='mindcube_000123', source='MindCube', question='Which object is behind the chair?', question_type='mindcube_rotation')]
try:
    _, r = P.read_bank(*bank(items, dict(banks=['dev-S1'], venue='x')), registry_pin=reg, prereg_pin=prereg); out['outside_scope_relabelled_dev'] = 'ADMITTED label='+r['label']
except ValueError as e: out['outside_scope_relabelled_dev'] = 'refused: '+str(e)
# 2. ReVSI items + deployed selector used but not declared in choices
items = [dict(id='revsi_1', question_type='object_abs_distance')]
try:
    P.read_bank(*bank(items, dict(banks=['ReVSI'], venue='1')), registry_pin=reg, prereg_pin=prereg, choices=())
    out['revsi_selector_undeclared_no_freeze'] = 'ADMITTED'
except ValueError as e: out['revsi_selector_undeclared_no_freeze'] = 'refused: '+str(e)
# 3. VSI-Bench item relabelled as VSTI camera type to use the no-freeze camera exception
items = [dict(id='vsibench_abs_1', question_type='camera_displacement')]
try:
    P.read_bank(*bank(items, dict(banks=['VSTI'], venue='1')), registry_pin=reg, prereg_pin=prereg, camera_routing=True)
    out['camera_exception_relabel'] = 'ADMITTED (no freeze)'
except ValueError as e: out['camera_exception_relabel'] = 'refused: '+str(e)
print(json.dumps(out, indent=1))
json.dump(out, open('/scratch/jjyeung/orch_n30/review_tree/work/h/PROBE_BANK.json','w'), indent=1)
