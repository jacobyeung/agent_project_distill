from common import *
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
seal=J.load(W/'ext/pwrap/k/7.json')
assert inventory(D/'p_tree')==seal['files']
roots=[L/'work/build24m4i/inputs',L/'work/build24m4h/inputs',W/'w24g/work/build24m4g/inputs',W/'w24/work/build24m4/hidden/inputs',W/'w24/work/build24m3/hidden/inputs',W/'w24/work/build24m3/hidden/payload',L/'work/build24m4d/inputs',L/'work/build24m4d/upload/u']
def get(h):
 for d in roots:
  p=d/h
  if p.is_file():
   J.checked(p,h);q=D/'inputs'/h
   if not q.exists():q.write_bytes(p.read_bytes())
   return J.load(q)
 raise ValueError('LOCAL_INPUT_MISSING:'+h)
p=get('b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad')
r=get('0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a')
s=get('5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af')
model=get(r['base_model']['sha256'])
print('P config recipe selection authenticated; model',json.dumps(model,indent=2))
for field in ('tokenizer_config.json','processor_config.json','config.json','preprocessor_config.json'):
 if field in model['files']:
  try:print(field,json.dumps(get(model['files'][field]),indent=2)[:1500])
  except ValueError as e:print(str(e))
J.write(D/'P_AUTH.json',dict(tree=digest(seal['files']),file_inventory_equal=True,original_archive_sha256=seal['archive']['sha256'],local_archive_sha256=J.sha(L/'work/build24m4h/p.tar'),local_archive_original=False,selection=J.sha(D/'inputs'/'5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'),recipe=r,model=model))
