from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import sys,runpy,json
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
sys.path[:0]=[str(L/'work/build24/kits/n/b'),str(L/'work/build24'),str(L/'work/tree_r1')]
import z,joblib as J
from student_pilot.carrier_c1_run import identity
from launch_r1.entry import ASSERTIONS
base=J.load(D/'review_tests/no_pass/node/q_22c714e1_91/prepared.json')
cases=[('pass',None),('missing','R1_HOST_RECEIPT_MISSING'),('path','R1_HOST_RECEIPT_PATH_DIFFERS'),
    ('sha','R1_HOST_RECEIPT_INVALID'),('status','R1_HOST_RECEIPT_NOT_PASS'),('identity','R1_HOST_IDENTITY_DIFFERS'),
    ('assertions','R1_HOST_ASSERTIONS_INCOMPLETE'),('audit','R1_HOST_LOADER_AUDIT_INCOMPLETE'),('symlink','R1_HOST_RECEIPT_MISSING')]
records=[]
for name,expected in cases:
 r=D/'host_pin_tests'/name;(r/'q').mkdir(parents=True);(r/'s').symlink_to(L/'work/tree_r1',target_is_directory=True)
 cfg=deepcopy(base);host=dict(status='PASS',config_identity=identity(cfg),assertions=dict.fromkeys(ASSERTIONS,True),loader_audit={'complete':True})
 if name=='status':host['status']='FAIL'
 if name=='identity':host['config_identity']='0'*64
 if name=='assertions':host['assertions'].pop(ASSERTIONS[0])
 if name=='audit':host['loader_audit']['complete']=False
 pin=J.write(r/'q/host.json',host)
 if name=='sha':pin['sha256']='0'*64
 if name=='path':pin['path']=str(r/'host.json')
 if name=='symlink':
  (r/'q/host.json').rename(r/'q/receipt.json');(r/'q/host.json').symlink_to(r/'q/receipt.json')
 result=dict(status='ADMIT',init_milestone=400,config=J.write(r/'config.json',cfg),host_receipt=pin)
 if name=='missing':result.pop('host_receipt')
 J.write(r/'q/RESULT.json',result)
 code=None
 with patch.object(sys,'argv',['h.py',str(r),str(r/'v.json')]):
  try:runpy.run_path(str(L/'work/build24/kits/n/b/h.py'),run_name='__main__')
  except ValueError as e:code=str(e)
 assert code==expected,(name,code,expected)
 if not expected:
  final=J.load(r/'v.json');assert identity(final)==identity(cfg)
  assert J.load(final['r1_training']['host_receipt']['path'])==host
 records.append(dict(case=name,refusal=code))
J.write(D/'HOST_PIN_TESTS.json',dict(status='PASS',records=records))
print('exact native host pin and all host refusals PASS')
