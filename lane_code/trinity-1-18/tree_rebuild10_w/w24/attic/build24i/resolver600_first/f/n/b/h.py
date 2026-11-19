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
if not isinstance(host,dict):raise ValueError('R1_HOST_RECEIPT_INVALID')
if host.get('status')!='PASS':raise ValueError('R1_HOST_RECEIPT_NOT_PASS')
if host.get('config_identity')!=value:raise ValueError('R1_HOST_IDENTITY_DIFFERS')
if not isinstance(host.get('assertions'),dict) or set(host['assertions'])!=set(ASSERTIONS) or not all(v is True for v in host['assertions'].values()):raise ValueError('R1_HOST_ASSERTIONS_INCOMPLETE')
if not isinstance(host.get('loader_audit'),dict) or host['loader_audit'].get('complete') is not True:raise ValueError('R1_HOST_LOADER_AUDIT_INCOMPLETE')
# Host evidence is pinned before the prepared config is published.
cfg['r1_training']['host_receipt']=write(r/'hr.json',host)
from rv import sync_preparation
sync_preparation(cfg,r,'ph.json')
if identity(cfg)!=value:raise ValueError('R1_HOST_IDENTITY_DIFFERS')
write(sys.argv[2],cfg)
