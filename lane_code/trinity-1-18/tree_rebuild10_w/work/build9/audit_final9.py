import hashlib,json,runpy,sys
from fractions import Fraction
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build9';T=L/'work/tree_r1';P=B/'proofs/audit';P.mkdir(parents=True,exist_ok=True)
prior=json.loads((L/'work/build8/proofs/audit/INFERENCE_COMPONENTS.json').read_text())
(P/'INFERENCE_COMPONENTS.json').write_text(json.dumps({'scope':prior['seed_scope'],'seed_scope':prior['seed_scope']}))
runpy.run_path(str(B/'inference_inventory.py'),run_name='__main__')
runpy.run_path(str(B/'review_evidence.py'),run_name='__main__')
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,file_pin
counts=json.loads((B/'proofs/row_counts/RESULT.json').read_text())
original=load(L/'out/MIX_A0.json');records={}
for arm in ('a2','a0'):
    root=B/'kits'/arm;launch=load(root/'k/launch.json');cfg=load(root/launch['config']['file'])
    mix=load(root/cfg['r2_build2']['mix']['path'])
    cells={c['type']:c for c in mix['cells'] if c['type'] in ('recovery','units')}
    prior_cells={c['type']:c for c in original['cells'] if c['type'] in cells}
    assert cells==prior_cells
    assert cfg['b7_inputs']['routing_training_counts']==counts['training_counts']
    assert not cfg.get('h1',{}).get('faithful_own_camera_rows',False)
    records[arm]=dict(config=file_pin(root/launch['config']['file']),mix=cfg['r2_build2']['mix'],
        cells=cells,counts=counts['training_counts'],go=launch['production_authorized'],
        blockers=cfg['b7_blockers'],conditional_expected=counts['expected'][arm])
(B/'proofs/row_counts/MIX_BOUND.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(dict(kits=list(records),mix_bound=True)))
