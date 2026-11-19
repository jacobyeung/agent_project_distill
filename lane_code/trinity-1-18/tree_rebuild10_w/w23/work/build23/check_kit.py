from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build21';D=L/'work/build23';K=B/'kits/q'
sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J
from naming21 import scan_decoded
from student_pilot.p3_provenance import digest
from student_pilot.source_seal import inventory,check_archive
from student_pilot.r1_persisted import scope
from student_pilot.r1_coverage import validate_binding,source_names
record=J.load(D/'KIT.json');cfg=J.load(K/'k/n.json')
assert J.seal(K)==record['kit_seal']
files=inventory(L/'work/tree_r1');assert digest(files)==record['tree_seal']
control=J.load(K/'k/a.json');check_archive(dict(path=str(K/control['source']['path']),sha256=control['source']['sha256']),files)
uploads=J.load(B/'UPLOADS.json');paths={x['sha256']:x['local_path'] for x in uploads['files']}
with scope(paths):
    validate_binding(cfg)
    assert source_names({},cfg)==()
    from student_pilot.r1_mix import validate_binding as sampler_binding
    try:sampler_binding(cfg['r2_sampling'])
    except ValueError as error:assert str(error)=='R1_COMPLETE_FILTERED_POPULATION_REQUIRED',str(error)
    else:raise AssertionError('Unpopulated kit admitted a training sampler')
scan=scan_decoded(K);J.write(D/'SCAN.json',scan)
assert scan['status']=='PASS'
print(json.dumps(dict(status='PASS',kit=record['kit_seal'],tree=record['tree_seal'],strings=scan.get('checked_strings'))))
s=(D/'lookahead_before.py').read_text().replace('LOOKAHEAD_BEFORE.json','LOOKAHEAD_AFTER.json')
s=s.replace("ns+'/kitq'", "ns+'/minimal'").replace("node/'kitq/q/RESULT.json'", "node/'minimal/q/RESULT.json'")
(D/'lookahead_after.py').write_text(s)
