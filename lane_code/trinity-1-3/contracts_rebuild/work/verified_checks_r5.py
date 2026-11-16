from pathlib import Path
import shutil,subprocess,sys
L=Path(__file__).resolve().parents[1]
for rel in ('student_pilot/training_contract.py','student_pilot/live_trace313.py','student_pilot/phrases.py'):
    p=L/'work/trees/r5_applied'/rel;q=p.with_suffix('.release');shutil.copyfile(L/'work/src_r5'/rel,q);q.replace(p)
s=(L/'work/apply_proof_r5.py').read_text().replace('r5_proof','r5_verified_proof').replace('r5_snapshot','r5_verified_snapshot')
(L/'work/apply_verified_r5.py').write_text(s)
p=L/'work/trees/r5_verified_proof/base';p.parent.mkdir(exist_ok=True);shutil.copytree(L/'work/base/work/base/tree_b01ce449',p)
for f in [p,*p.rglob('*')]:f.chmod(f.stat().st_mode & ~0o222)
for name in ('build_packet_r5.py','apply_verified_r5.py'):
    subprocess.run([sys.executable,'-I','-s','-B',str(L/'work'/name)],check=True)
