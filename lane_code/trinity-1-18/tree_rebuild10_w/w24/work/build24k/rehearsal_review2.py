"""Attach only the synthetic review, through the supplied kit's native rv.run."""
from pathlib import Path
import os,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths2 import L,D,R,NS
root=Path(NS);kit=root/'kit_n_go'
sys.path[:0]=[str(root/'p2/s'),str(kit/'b'),str(L/'work/build24')]
import joblib as J
from student_pilot.carrier_c1_run import identity
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import pinned,file_pin,load
import rv
cfg=J.load(root/'v.json');request=J.load(root/'r.json');result=J.load(root/'p2/q/RESULT.json')
native=result['host_receipt'];assert file_pin(root/'p2/q/host.json')==native
assert load(pinned(cfg['r1_training']['host_receipt']))==load(pinned(native))
value=identity(cfg);review=R/'target/n_r';review.mkdir(mode=0o700);review.chmod(0o700)
fd=os.open(review/'review.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as stream:
    os.fchmod(stream.fileno(),0o600)
    json.dump(dict(verdict='PASS',config_identity=value,evidence=dict(scope='synthetic CPU fixture only',native_host=native)),stream)
with scope(request['_paths']),scope(cfg['r1_training']['persisted_files']):
    assert rv.run(kit,root,root/'v.json','91',interval=1)==0
cfg=J.load(root/'v.json');assert identity(cfg)==value
J.write(root/'gates.json',dict(status='PASS',identity=value,host_source=native,
    host_written_by='launch_r1.production_proof',fixture_receipts=['review'],review_consumer='kit b/rv.py',production_gates_supplied=False))
