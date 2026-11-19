"""Authenticate unchanged contracts and qualify unavailable historical proofs."""
from pathlib import Path
import json,hashlib,sys,re
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1';old=L/'work/build14'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
base=load(B/'BASE14_SEAL.json')
changed=[n for n,h in base['files'].items() if sha(T/n)!=h]
assert set(changed)=={'student_pilot/r1_handover.py','student_pilot/r2_openers.py'},changed
receipt=load(old/'proofs/final/suite_tree/r2/GROUP_RECEIPT.json')['inputs']
fixtures={n:sha(L/'fixtures'/n) for n in receipt['fixtures']}
assert fixtures==receipt['fixtures']
inputs={n:sha(L/n) for n in receipt['bound_n1_inputs']}
slices={n:sha(L/n) for n in receipt['bound_real_slices']}
assert inputs==receipt['bound_n1_inputs'] and slices==receipt['bound_real_slices']
assert sha(L/'work/n1fix2/test_runner.py')==receipt['runner_sha256']
stable={n:sha(T/n) for n in base['files'] if n not in changed}
cfg=load(B/'inputs/kit_config.json')
sys.path.insert(0,str(T))
from student_pilot.r1_handover import pin_values
assert pin_values(cfg)==pin_values(load(old/'inputs/kit_config.json'))
assert cfg['init_artifact']['artifact']['sha256'].startswith('1d6eeb28')
assert cfg['camera_overrides']=={'weight_focal':2.0,'weight_scale':.04}
unavailable={
 'census':'/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite',
 'native_builder':'/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl',
 'recompose':'/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl',
 'encode':'/scratch/jjyeung/orch_n30/rows_r1/out/recovery_v3/rows.jsonl',
 'mapping':'/scratch/jjyeung/orch_n30/r1_ops/work/snap_fac07052/work/tree/student_pilot/type_mix.py',
 'depth_sweep':'/scratch/jjyeung/orch_n30/review_tree11/work/parity/geo_dump.py',
}
records={}
for name,missing in unavailable.items():
    assert not Path(missing).exists(),missing
    root=old/'proofs'/dict(native_builder='builder',recompose='composition').get(name,name)
    driver=old/(name+'14.py')
    if name=='depth_sweep':root=L/'work/build12/proofs/depth_sweep';driver=L/'work/build12/sweep.py'
    records[name]={'status':'not rerun: input absent ('+missing+')','build15_pass':False,
        'historical_files':{str(p.relative_to(L)):sha(p) for p in root.glob('*.json')},
        'driver':str(driver.relative_to(L)),'driver_sha256':sha(driver) if driver.exists() else None}
    observed=root/'hits.json';hashes=root/'source_hashes.json'
    if observed.exists() and hashes.exists():
        used=load(observed);prior=load(hashes)
        mismatch=[n for n in used if n in prior and (not (T/n).is_file() or sha(T/n)!=prior[n])]
        records[name].update(observed_source_mismatches=mismatch,
            inherited_result_qualified=not mismatch,
            unchanged_observed_sources={n:prior[n] for n in used if n in prior and n not in mismatch})
    else:
        records[name].update(inherited_result_qualified=False,
            reason='Historical record retained; complete source/runner binding unavailable, so no transferred qualification.')
    records[name]['fixture_binding']='All bound fixtures and local inputs equal build 14; missing external bytes remain unverified and their pins are unchanged.'
    prior_driver=L.parent/'w14'/driver.relative_to(L)
    records[name]['runner_unchanged']=driver.exists() and prior_driver.exists() and sha(driver)==sha(prior_driver)
    records[name]['inherited_result_qualified'] &= records[name]['runner_unchanged']
    destination=B/'proofs'/name;destination.mkdir(parents=True,exist_ok=True)
    (destination/'NOT_RERUN.json').write_text(json.dumps(records[name],indent=2))
value=dict(base14_seal=base['tree_sha256'],changed_existing=changed,unchanged_source_hashes=stable,
    fixture_hashes=fixtures,bound_inputs=inputs,bound_slices=slices,runner_sha256=receipt['runner_sha256'],
    kit_input_sha256=sha(B/'inputs/kit_config.json'),step544_parent=cfg['init_artifact']['artifact'],
    unavailable=records)
(B/'PRESERVATION.json').write_text(json.dumps(value,indent=2))
print(json.dumps({k:v['status'] for k,v in records.items()},indent=2))
