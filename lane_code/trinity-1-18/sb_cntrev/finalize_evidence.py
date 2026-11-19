"""Attach review provenance without changing the kit's measured scores or execution manifests."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
inputs={}
for folder in ['inputs','kit/files','kit/work']:
 for p in sorted((root/folder).iterdir()):
  if p.is_file():inputs[str(p)]=sha(p)
for name in ['audit_cpu.py','audit_controls.py','finalize_evidence.py']:
 p=root/name;inputs[str(p)]=sha(p)
mirror=Path('/scratch/jjyeung/n30_mirror/b05_owngrd/B05_K1_TEACHER_LABELS.tar');inputs[str(mirror)]=sha(mirror)
code=Path('/scratch/jjyeung/orch_n30/b05_owngrd/code/owngrd')
for name in ['teacher.py','stub_tower.py','common.py','vendor/sam3_tower.py','vendor/sam_backend.py','vendor/SAM3_RECEIPT.json']:
 p=code/name;inputs[str(p)]=sha(p)
mfile=root/'out/MANIFEST_R0DEV.json';m=json.loads(mfile.read_text());inputs[str(mfile)]=sha(mfile)
for c in m['captures']:
 for f in c['frames']:inputs[f['path']]=f['sha256']
 fp=Path('/scratch/jjyeung/orch_n30/b10_reserve/out/frame_manifests')/(c['canonical'].split('/',1)[1]+'.json')
 inputs[str(fp)]=sha(fp)
# Reuse the checkpoint digest already computed by sha256sum; do not repeat the 3.45 GB read.
weightline=(root/'out/weights.sha256').read_text().split()
inputs[weightline[1]]=weightline[0]
scorepath=root/'out/STUB_SCORE.json';score=json.loads(scorepath.read_text())
scoreinputs={str(root/'kit/files/COUNT_ITEMS_535.jsonl'):inputs[str(root/'kit/files/COUNT_ITEMS_535.jsonl')],str(root/'kit/files/score_count_pricing.py'):inputs[str(root/'kit/files/score_count_pricing.py')],str(mfile):inputs[str(mfile)]}
for p in sorted((root/'out/stub_r0dev').glob('*/teacher.json.gz')):scoreinputs[str(p)]=sha(p)
score['review_provenance']={'inputs_sha256':scoreinputs,'annotation':'Added after the unmodified kit scored CPU stub outputs; all original score fields are unchanged.'}
scorepath.write_text(json.dumps(score,indent=1)+'\n')
for f in ['CPU_AUDIT.json','CONTROL_AUDIT.json']:
 p=root/'out'/f
 doc=json.loads(p.read_text());inputs.update(doc['inputs_sha256']);inputs[str(p)]=sha(p)
outputs={str(p):sha(p) for p in sorted((root/'out').iterdir()) if p.is_file() and p.name!='PROVENANCE.json'}
json.dump({'inputs_sha256':inputs,'outputs_sha256':outputs,'scope':'CPU read-only review; input frame hashes were verified by the kit manifest builder. Extracted supplied JSON files are evidence inputs and remain unchanged. The production manifest and runner completion files retain their native frame/item/manifest/contract checksum fields.','command':'nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 python3 finalize_evidence.py'},open(root/'out/PROVENANCE.json','w'),indent=2)
print('provenance inputs',len(inputs),'outputs',len(outputs))
print('verdict lines',len((root/'out/REVIEW_VERDICT.md').read_text().splitlines()))
assert len((root/'out/REVIEW_VERDICT.md').read_text().splitlines())<=50
assert score['coverage']['with_teacher']==385
assert json.loads((root/'out/CONTROL_AUDIT.json').read_text())['teacher_outputs']==0
