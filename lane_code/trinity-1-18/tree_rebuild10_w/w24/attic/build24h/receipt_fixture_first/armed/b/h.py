import hashlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from z import load,checked,seal,write
k=Path(__file__).resolve().parents[1];seal(k)
if len(sys.argv)!=3:raise ValueError('E84')
r=Path(sys.argv[1]);q=load(r/'q/RESULT.json')
if q.get('status')!='ADMIT' or q.get('init_milestone')!=400:raise ValueError('E81')
p=q['config'];cfg=load(checked(p['path'],p['sha256']))
if cfg.get('world_size')!=4 or cfg.get('r1_training',{}).get('init_policy')!='step400_export_weights_fresh_v1':raise ValueError('E85')
sys.path.insert(0,str(r/'s'))
from student_pilot.carrier_c1_run import identity
from launch_r1.entry import ASSERTIONS
value=identity(cfg)
source=r/'host.json'
if not source.is_file() or source.is_symlink():raise ValueError('R1_HOST_RECEIPT_MISSING')
try:host=load(source)
except (ValueError,OSError):raise ValueError('R1_HOST_RECEIPT_INVALID') from None
if host.get('status')!='PASS':raise ValueError('R1_HOST_RECEIPT_NOT_PASS')
if host.get('config_identity')!=value:raise ValueError('R1_HOST_IDENTITY_DIFFERS')
if set(host.get('assertions',{}))!=set(ASSERTIONS) or not all(v is True for v in host['assertions'].values()):raise ValueError('R1_HOST_ASSERTIONS_INCOMPLETE')
if host.get('loader_audit',{}).get('complete') is not True:raise ValueError('R1_HOST_LOADER_AUDIT_INCOMPLETE')
control=load(k/'k/a.json');pin=control.get('review')
if not isinstance(pin,dict) or set(pin)!={'path','sha256'}:raise ValueError('R1_REVIEW_RECEIPT_MISSING')
h=pin['sha256']
if not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h) or pin['path']!='u/'+h:raise ValueError('R1_REVIEW_PIN_INVALID')
source=r.parent/pin['path']
if not source.is_file() or source.is_symlink():raise ValueError('R1_REVIEW_RECEIPT_MISSING')
raw=source.read_bytes()
if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('R1_REVIEW_RECEIPT_CHANGED')
try:
 import json
 review=json.loads(raw)
except (ValueError,UnicodeError):raise ValueError('R1_REVIEW_RECEIPT_INVALID') from None
if not isinstance(review,dict) or review.get('verdict')!='PASS':raise ValueError('R1_REVIEW_RECEIPT_NOT_PASS')
if review.get('config_identity')!=value:raise ValueError('R1_REVIEW_IDENTITY_DIFFERS')
# Pins refer to job-private snapshots. Re-read the staged bytes only once.
host_pin=write(r/'hr.json',host)
review_path=r/'rv.json';review_path.write_bytes(raw)
cfg['r1_training']['host_receipt']=host_pin
cfg['r1_training']['review']={'path':str(review_path),'sha256':h}
if identity(cfg)!=value:raise ValueError('R1_REVIEW_IDENTITY_DIFFERS')
write(sys.argv[2],cfg)
