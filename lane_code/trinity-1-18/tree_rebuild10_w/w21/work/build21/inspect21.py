from pathlib import Path
import sys,json
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,pinned
c=load(L/'work/build21/inputs/config.json');s=load(pinned(c['r1_training']['row_sources']))
print('sources',json.dumps(s,indent=2));print('extent',c['extent_receipt'])
for name,path in [('units',Path('/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h/COVERAGE_UNITS_V2H.jsonl')),('distance',Path('/scratch/jjyeung/n30_mirror/dist_diag/coverage_v2h/COVERAGE_DISTANCE_V2H.jsonl'))]:
 with path.open() as f:r=json.loads(next(f))
 print(name,'keys',list(r));print('identity',r['qid'],r['candidate_id']);print('prov',json.dumps(r['provenance']));print('record keys',list(r.get('ground_record',{})))
print('extent keys',list(load(pinned(c['extent_receipt']))))
