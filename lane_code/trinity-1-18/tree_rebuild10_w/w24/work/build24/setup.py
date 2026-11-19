from pathlib import Path
import json, shutil, tarfile
L=Path(__file__).resolve().parents[2];D=L/'work/build24';A=L/'attic/build24'
with tarfile.open(L.parent/'w23/out/tree_rebuild_b23_40abf77b.tar') as t:
    for name in ('work/build21/joblib.py','work/build23/tests23.py'):
        target=D/Path(name).name
        target.write_bytes(t.extractfile(name).read())
for name in ('r1_coverage.py','r1_population.py','r1_rooms.py','s1_admission.py'):
    p=L/'work/tree_r1/student_pilot'/name
    if p.with_suffix('.py.orig').exists():p.with_suffix('.py.orig').rename(A/(name+'.orig'))
for name in ('production_proof.py','entry.py','build.py'):
    p=L/'work/tree_r1/launch_r1'/name
    if p.with_suffix('.py.orig').exists():p.with_suffix('.py.orig').rename(A/(name+'.orig'))
shutil.copyfile(D/'joblib.py',A/'joblib23.py')
(D/'START.json').write_text(json.dumps(dict(workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file()),base='build22 d41a6dc8')))
print('Prepared build24 scripts and preserved merge baselines.')
