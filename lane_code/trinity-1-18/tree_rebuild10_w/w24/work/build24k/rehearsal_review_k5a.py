"""Attach only the synthetic review, through the supplied kit's native rv.run."""
from pathlib import Path
import os,sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rehearsal_paths_k5a import L,D,R,NS
root=Path(NS);kit=root/'kit_n_go'
sys.path[:0]=[str(root/'p2/s'),str(kit/'b'),str(L/'work/build24')]
import joblib as J
from student_pilot.carrier_c1_run import identity
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import pinned,file_pin,load
import rv
cfg=J.load(root/'v.json');request=J.load(root/'r.json');result=J.load(root/'p2/q/RESULT.json')
native=result['host_receipt'];assert file_pin(root/'p2/q/host.json')==native
bound_host=load(pinned(cfg['r1_training']['host_receipt'])); native_host=load(pinned(native))
assert all(bound_host[k]==v for k,v in native_host.items())
assert bound_host['protected_census']==rv.__dict__.get('_unused',bound_host['protected_census'])
value=identity(cfg);review=R/'target/n_r';review.mkdir(mode=0o700);review.chmod(0o700)
# The fixture reviewer installs its receipt only after native publication/wait.
import threading,time
review_errors=[]
def reviewer():
    try:
        live,_=rv.location(kit,root,'91')
        deadline=time.monotonic()+600
        while not (live/'WAITING_REVIEW.json').exists():
            if time.monotonic()>deadline:raise RuntimeError('Native review wait not reached')
            time.sleep(0.2)
        waiting=J.load(live/'WAITING_REVIEW.json')
        assert waiting['identity']==value and waiting['v_sha256']==J.sha(live/'v.json')
        fd=os.open(review/'review.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:
            os.fchmod(stream.fileno(),0o600)
            json.dump(dict(verdict='PASS',config_identity=value,evidence=dict(scope='synthetic CPU fixture only',native_host=native)),stream)
        J.write(root/'FIXTURE_REVIEWER.json',dict(wait_observed=True,publication_sha256=waiting['v_sha256'],review=J.sha(review/'review.json')))
    except Exception as error:review_errors.append(str(error))
worker=threading.Thread(target=reviewer,daemon=True);worker.start()
with scope(request['_paths']),scope(cfg['r1_training']['persisted_files']):
    assert rv.run(kit,root,root/'v.json','91',interval=1)==0
worker.join(timeout=2);assert not worker.is_alive() and not review_errors,review_errors
cfg=J.load(root/'v.json');assert identity(cfg)==value
J.write(root/'gates.json',dict(status='PASS',identity=value,host_source=native,
    host_written_by='launch_r1.production_proof',fixture_receipts=['review'],review_consumer='kit b/rv.py',production_gates_supplied=False))
