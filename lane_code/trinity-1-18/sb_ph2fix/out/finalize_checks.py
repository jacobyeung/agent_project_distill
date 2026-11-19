"""Refresh rerun staging evidence and check the launcher's production preflight without GPU access."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'sb_mask_phrase/part2'))
import launch_gpu as L


def main():
    stage=ROOT/'out/STAGING_PART2.json'
    assert json.loads(stage.read_text())['status']=='PASS'
    assert json.loads((ROOT/'out/STAGED_SMOKE.json').read_text())['status']=='PASS'
    assert L.sha(L.KIT/'part2/gate.py')=='f40b93d12e79768eea1ee6b2b2911695fcc64b4f935e9c4589bcd8b20a5a8368'
    pins=L.preflight(L.KIT)
    assert L.admit_state(L.KIT/'out/pool_part2')==0
    pins[str(Path(__file__))]=L.sha(Path(__file__))
    result=dict(status='PASS',gpu='NOT PROBED',vnice='HASH CHECKED; NOT EXECUTED',
                command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 python -B out/finalize_checks.py',
                input_sha256=pins)
    (ROOT/'out/LAUNCH_PREFLIGHT.json').write_text(json.dumps(result,indent=1)+'\n')
    cpu=ROOT/'out/CPU_VALIDATION.json'
    original=ROOT/'out/CPU_VALIDATION_BEFORE_STAGING_REFRESH.json'
    original.write_bytes(cpu.read_bytes())
    record=json.loads(cpu.read_text())
    record['staging_refresh']=dict(command='env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 bash sb_mask_phrase/run.sh part2/staging.py',
                                  reason='Include staged SciPy reader dependency and final control files',status='PASS')
    record['input_sha256'][str(original)]=L.sha(original)
    for p in (stage,L.KIT/'part2/staging.py',ROOT/'out/final_staging.log',ROOT/'out/STAGED_SMOKE.json',ROOT/'out/LAUNCH_PREFLIGHT.json'):
        record['input_sha256'][str(p)]=L.sha(p)
    cpu.write_text(json.dumps(record,indent=1)+'\n')
    print('PASS: production preflight, fresh output state, frozen guard, refreshed staging receipts')

if __name__=='__main__':main()
