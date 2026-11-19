"""Record the completed human-facing sample review; preserve unavailable checks."""
import json,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'out'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(OUT/'READ30.md')=='5d74330da1cf9096341805bbe214342845073593b51f14e9c5feed156d521e8e', 'The sample changed; manual review must be repeated.'
rows=[json.loads(s) for s in re.findall(r'```json\n(.*?)\n```',(OUT/'READ30.md').read_text(),re.S)]
assert len(rows)==30
review=dict(status='PASS',reviewer='Codex primary agent',scope='30 complete evaluation items and final wording text; no source pose recomputation',
 reviewed_items=[x['id'] for x in rows],wordings_covered=24,
 findings='Frame pairs and clip counts agree with question text. Displacement uses meters and endpoint distance. Rotation specifies degrees, left-positive signs and (-180, 180]. Direction questions retain the starting orientation and all ordered answer options. Grammar is acceptable.',
 training_read30='MISSING: authenticated camera training rows unavailable',
 input_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),OUT/'READ30.md',OUT/'HELDOUT_CAMERA_ITEMS.json',OUT/'WORDINGS.json']})
(OUT/'MANUAL_REVIEW.json').write_text(json.dumps(review,indent=2)+'\n')
p=OUT/'CHECKS.json';c=json.loads(p.read_text())
c['heldout']['read30']='PASS: 30 complete evaluation items manually read; all 24 wordings covered'
c['heldout']['native_loader']={'status':'NOT_RUN','reason':'MISSING Python package torch in the available interpreter'}
c['heldout']['ground_truth_recomputation']='NOT_RUN: source evaluation labels are preserved, not independently recomputed from poses'
c['manual_review']={'path':str(OUT/'MANUAL_REVIEW.json'),'sha256':sha(OUT/'MANUAL_REVIEW.json')}
c['input_sha256'].update({str(OUT/'MANUAL_REVIEW.json'):sha(OUT/'MANUAL_REVIEW.json'),str(Path(__file__).resolve()):sha(__file__)})
p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
(ROOT/'STATUS.md').write_text('Delivery: the 900-item held-out camera set and native-task twins pass independent CPU metadata checks and the full 30-item wording review. The inventory reserves 40 training wordings and 8 held-out wordings per type. All 120 training cells remain MISSING because N’s pinned camera routing payload is absent; no training rows are certified. Native loader admission requires the missing torch dependency. The report and cont_ops18 handoff describe integration and the exact missing inputs.\n')
