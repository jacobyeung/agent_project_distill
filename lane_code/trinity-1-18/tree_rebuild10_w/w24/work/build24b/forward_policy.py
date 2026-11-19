from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[2];name='student_pilot/r1_components.py';p=L/'work/tree_r1'/name;a=L/'attic/build24b/tree'/name
assert not a.exists();shutil.copyfile(p,a)
s=p.read_text().replace('from .r1_persisted import verify, scope','from .r1_persisted import verify, scope, init_policy').replace("proof_mode=value.get('proof_mode'))", "proof_mode=value.get('proof_mode'),init_policy=init_policy(value))")
p.write_text(s)
