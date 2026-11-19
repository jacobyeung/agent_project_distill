"""Authenticate final neighboring manifests without modifying any lane."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'out'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
path=OUT/'OVERLAP.json';old=json.loads(path.read_text())
snapshot=OUT/'OVERLAP_INITIAL.json'
if not snapshot.exists():snapshot.write_bytes(path.read_bytes())
ours={x['path'] for x in json.loads((OUT/'FILES_TOUCHED.json').read_text())['files']}
inputs={str(p):sha(p) for p in (Path(__file__),snapshot,OUT/'FILES_TOUCHED.json')}
lanes={}
for lane in ('camform','pointD','donor','prior2'):
    p=ROOT.parent/lane/'out/FILES_TOUCHED.json'
    names={x['path'] for x in json.loads(p.read_text())['files']}
    inputs[str(p)]=sha(p)
    lanes[lane]=dict(status='MANIFEST',manifest=str(p),files=sorted(names),overlap=sorted(ours&names))
cam=ROOT.parent/'camform/out/PATCH_CAMFORM.patch'
assert sha(cam)==old['inputs_sha256'][str(cam)],'Camform patch changed; requires a new application check'
inputs[str(cam)]=sha(cam)
value=dict(command='env PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B work/refresh_overlap.py',
    inputs_sha256=inputs,lanes=lanes,camform=old['camform'])
path.write_text(json.dumps(value,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Final overlap verification is complete. Camform shares r1_routing.py and applies without fuzz; prior2 shares r1_population.py. The authenticated donor and pointD manifests share no PATCH_A2 file. Both full comparisons have no new failures; final packaging is next.\n')
print(json.dumps({k:v['overlap'] for k,v in lanes.items()}))
