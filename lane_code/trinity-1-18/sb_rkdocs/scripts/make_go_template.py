"""Print identity fields; generate a non-authorizing GO template."""
from gates import *
from common import *
m=W/'configs/R0DEV_ROOM_MANIFEST.json';p=W/'configs/KERNEL_PROVENANCE.json';r=W/'configs/READER_RECEIPT.json';ins={str(x):sha(x) for x in [m,p,r]};ins.update(run_code_hashes())
record=dict(decision='NOT_GO',host='trinity-1-18',gpu_uuid='MISSING',run_id='MISSING',manifest_sha256=sha(m),code_sha256=digest(run_code_hashes()),settings_sha256=digest(SETTINGS),provenance_sha256=sha(p),reader_receipt_sha256=sha(r),max_gpu_seconds=5400,allocation_samples=[])
write(W/'configs/GO.template.json',record,ins);print(json.dumps(record,indent=2))
