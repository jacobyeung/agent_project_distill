from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];D=L/'work/build23b';B=L/'work/build21';T=L/'work/tree_r1';K=B/'kits/q'
sys.path[:0]=[str(T),str(B)]
import joblib as J
from naming21 import scan_decoded
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest,file_pin
from student_pilot.r1_persisted import scope
from student_pilot.r1_coverage import deferred,validate_binding
from student_pilot.r1_mix import validate_binding as sampler
kit=J.load(D/'KIT.json');assert J.seal(K)==kit['kit_seal'];assert digest(inventory(T))==kit['tree_seal']
control=J.load(K/'k/a.json');check_archive(file_pin(K/control['source']['path']),inventory(T))
paths={v['sha256']:v['local_path'] for v in J.load(B/'UPLOADS.json')['files']}
with scope(paths):
 cfg=J.load(K/'k/n.json');assert deferred(cfg,read_pins=True);validate_binding(cfg)
 try:sampler(cfg['r2_sampling'])
 except ValueError as e:assert str(e)=='R1_COMPLETE_FILTERED_POPULATION_REQUIRED'
 else:raise AssertionError('unprepared sampler admitted')
scan=scan_decoded(K)
assert scan['status']=='PASS',scan
# Keep the scanner decision and counts; its per-string inventory is reproducible.
summary={k:v for k,v in scan.items() if not isinstance(v,list)}
summary['list_counts']={k:len(v) for k,v in scan.items() if isinstance(v,list)}
summary.update(kit_seal=kit['kit_seal'],tree_seal=kit['tree_seal'])
J.write(D/'SCAN.json',summary);print(json.dumps(summary))
