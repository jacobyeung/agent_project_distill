from pathlib import Path
import sys
B=Path(__file__).resolve().parents[1];W=B.parents[1]/'work';K=B/'out/guard_kit'
sys.path.insert(0,str(K))
from guard_core import read,write,sha
pin=lambda p:dict(path=str(p.resolve()),sha256=sha(p))
family=dict(schema='g2-family-v1',release_ready=False,blockers=[
    'Complete job-visible naming migration is not validated; sealed runtime metadata still exposes legacy names.',
    'Whole-worker CPU namespace run has not completed.',
    'Independent review, current export closure and ORCH GO are required before launch.'],
    code_root=str(K),code_pins={str(p.relative_to(K)):sha(p) for p in sorted(K.rglob('*')) if p.is_file()},
    inputs={name:pin(B/'out/inputs'/name) for name in ('BASELINE_CONFIG.json','reference.json','items.json')},
    identity_source=pin(W/'from113/work/tree/student_pilot/carrier_c1_run.py'),
    baseline_artifact=pin(W/'from113/work/obj/m544_artifact.json'),
    time_limit='05:00:00',gpu_seconds=18000,
    publication=dict(kind='gcs',prefix='gs://cmu-gpucloud-jjyeung/q8/8c9d2e74',credentials='/project/community/jjyeung/gcloud',
                     pool='/project/community/jjyeung/okh7/a936d80c'))
write(B/'out/FAMILY.json',family)
