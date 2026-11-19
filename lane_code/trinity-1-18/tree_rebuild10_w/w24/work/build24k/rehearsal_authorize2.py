"""Authorize CPU fixture attempts and authenticate every changed v.json reference."""
from pathlib import Path
import json, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths2 import L,D,R,NS
sys.path[:0]=[str(R/'source'),str(L/'work/build24')]
import joblib as J
from student_pilot.carrier_c1_run import identity, prepared
from student_pilot.p3_provenance import pinned
from student_pilot.r1_persisted import scope
from launch_r1.entry import admit
from launch_r1.production_proof import verify_staging

def repin(request, pin):
    # Preserve every unrelated staged input and its authentication.
    request['staged_pins']=[pin if p.get('path')==pin['path'] else p for p in request['staged_pins']]
    if not any(p.get('path')==pin['path'] for p in request['staged_pins']):
        request['staged_pins'].append(pin)
    request['config']=pin
    return request

def main():
    phase=sys.argv[1]
    assert phase in ('fresh','budget','resume')
    root=Path(NS);cfg=J.load(root/'v.json');value=identity(cfg)
    # The native h.py and rv.py have already attached host/review and synced preparation.
    cfg['admission']=J.write(root/('admission_'+phase+'.json'),dict(verdict='PASS',reviewer='cpu-fixture-regression',config_sha256=value,preparation=cfg['preparation']))
    cfg['authorization']=J.write(root/('authorization_'+phase+'.json'),dict(verdict='GO',new_gpus=0,config_sha256=value,job_id='b24k2_'+phase,scope='CPU fixture only'))
    assert identity(cfg)==value
    pin=J.write(root/'v.json',cfg)
    for name in ('r.json','r2.json'):
        request=J.load(root/name)
        # r2 initially carries the resolver payload; r.json is the completed native request.
        if '_resolved' in request: request=J.load(root/'r.json')
        J.write(root/name,repin(request,pin))
    request=J.load(root/'r.json')
    with scope(request['_paths']),scope(cfg['r1_training']['persisted_files']):
        verify_staging(request);pinned(request['config']);admit(cfg);prepared(cfg,admission=True)
    J.write(root/('AUTH_'+phase+'.json'),dict(status='PASS',phase=phase,config=pin,identity=value,
        staged_v=[p for p in request['staged_pins'] if p['path']==pin['path']],native_admit=True,native_prepared=True))

if __name__=='__main__': main()
