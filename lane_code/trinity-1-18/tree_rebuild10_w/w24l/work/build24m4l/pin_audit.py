from common import *
import ast
from student_pilot.source_seal import inventory,check_archive
from student_pilot.p3_provenance import digest
from student_pilot.carrier_c1_run import identity
from launch_r1.build import verify
old=J.load(D/'DEPENDENT_PINS.json')['n'];stale={old['archive']['before']['sha256'],old['archive']['before']['tree_sha256'],old['code_file']['before']['sha256'],old['runtime_code']['before']}
results={}
for name in NAMES:
 k=kit(name);found=[]
 for p in (k/'k').glob('*.json'):
  try:value=J.load(p)
  except json.JSONDecodeError:value=base64.b64decode(json.loads(p.read_bytes())['payload']).decode()
  def visit(v,path):
   if isinstance(v,dict):
    if v.get('encoding')=='base64-json':visit(json.loads(base64.b64decode(v['payload'])),path+['decoded']);return
    if 'payload' in v and 'sha256' in v:
     try:visit(json.loads(base64.b64decode(v['payload'])),path+['embedded'])
     except (ValueError,TypeError):pass
    for key,item in v.items():visit(item,path+[key])
   elif isinstance(v,list):
    for i,item in enumerate(v):visit(item,path+[str(i)])
   elif isinstance(v,str):
    for h in stale:
     if h in v:found.append(dict(path='.'.join(path),hash=h))
  visit(value,[str(p.relative_to(k))])
 source=J.load(k/'k/a.json')['source'];code=J.load(k/'k/7.json');runtime=J.load(k/'k/c0.json')
 assert source['tree_sha256']==code['tree_sha256']==runtime['tree_sha256']==digest(inventory(T))
 check_archive(dict(path=str(k/source['path']),sha256=source['sha256']),inventory(T))
 assert J.load(k/'k/c.json')['code']['sha256']==J.sha(k/'k/7.json')
 assert J.load(k/'k/n.json')['code']['sha256']==J.load_raw(k/'k/c0.json')['sha256']==J.load(k/'k/p.json')['code_sha256']
 assert not found,(name,found)
 results[name]=dict(seal=verify(k),no_stale_pins=True,archive_verified=True,config_identity=identity(J.load(k/'k/c.json')))
J.write(D/'PIN_AUDIT.json',dict(status='PASS',kits=results))
print('PIN AUDIT PASS',results)
