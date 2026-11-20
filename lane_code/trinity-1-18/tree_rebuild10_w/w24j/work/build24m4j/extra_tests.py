from common import *
import subprocess,copy,importlib.util
from unittest.mock import patch
sys.path.insert(0,str(kit('qd')/'b'));import rb
F=D/'extra';F.mkdir()
# Confirm sites below the output root stay read-only and P's tree is read-only.
site=F/'site';site.mkdir();(site/'q_overlay.py').write_text('value=226\n')
control=F/'control.json';tree=D/'p_tree';env=rb.environment();env['paths'].insert(0,str(site));env['binds'].append(str(site))
J.write(control,dict(root=str(F),directory='x',environment=env,probe_only=True))
script=F/'mount_test.py';script.write_text('''import sys,json,errno
from pathlib import Path
value=json.loads(Path(sys.argv[1]).read_text())
sys.path[:0]=value['environment']['paths']
import q_overlay
assert q_overlay.value==226
for p in (Path(value['environment']['paths'][0])/'new',Path(sys.argv[2])/'new'):
 try:
  with p.open('w') as f:f.write('bad')
 except OSError as e:assert e.errno==errno.EROFS
 else:raise AssertionError('read-only binding lost')
(Path(value['root'])/'writable').write_text('ok')
print('MOUNTS PASS')
''')
cmd=rb.command(F,control,tree,{},env);cmd[-3]=str(script)
p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(F/'mounts.log').write_text(p.stdout);assert p.returncode==0,p.stdout
# Test both full-hash gates on native reconstruct(), with only input transport
# and the subprocess mocked. The output uses a deliberately wrong full hash.
pconfig=J.load(input_file('b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad'))
recipe=J.load(input_file('0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a'))
seal=J.load(W/'ext/pwrap/k/7.json');sp=J.write(F/'seal.json',seal)
receipt=J.write(F/'r.json',dict(database=dict(sha256=rb.DB,path='/tmp/none'),materialization=dict(path='r',sha256='0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a')))
paths={pconfig['code']['sha256']:sp['path'],pconfig['streams']['routing']['sha256']:receipt['path'],rb.TREE:str(L/'work/build24m4h/p.tar')}
for h in ('b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad','0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a','5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af'):paths[h]=str(input_file(h))
cfg=J.load(kit('qd')/'k/n.json');refusals=[]
for label,bad_hash in [('prefix','4e8e6c04'+'0'*56),('bytes',rb.DB)]:
 root=F/label;root.mkdir()
 def fake_run(*a,**kw):
  (root/'base').mkdir();(root/'base/rows.sqlite').write_bytes(b'wrong')
  J.write(root/'base/receipt.json',dict(database=dict(sha256=bad_hash)))
 with patch('student_pilot.p3_provenance.pinned',side_effect=lambda p:Path(paths[p['sha256']])),patch('student_pilot.source_seal.check_archive'),patch('student_pilot.source_seal.inventory',return_value=seal['files']),patch.object(rb,'mount_inputs',return_value={}),patch.object(rb.subprocess,'run',side_effect=fake_run):
  try:rb.reconstruct(cfg,root)
  except ValueError as e:
   wanted='P_TRAINED_ROUTING_RECONSTRUCTION_DIFFERS:'+rb.DB if label=='prefix' else 'E10:'
   assert str(e).startswith(wanted),str(e);refusals.append(str(e))
  else:raise AssertionError('Full hash gate accepted fixture')
# The arming delta must recreate the complete output from its declared baseline.
for path in (D/'arming_final/workspace/out/armed/UPLOADS_ROUTING_ARMED.json',D/'arming_final/workspace/out/native_armed/UPLOADS_ROUTING_ARMED.json'):
 if not path.exists():continue
 v=J.load(path);replay=copy.deepcopy(v['baseline_files'])
 for row in v['files']:
  n,rel=row['name'].split('/',1)
  if n in replay:replay[n][rel]=dict(sha256=row['sha256'],bytes=row['bytes'],mode=int(row['mode'],8))
 for n in ('q','n'):
  k=path.parent/'kits'/n
  expected={str(p.relative_to(k)):dict(sha256=J.sha(p),bytes=p.stat().st_size,mode=p.stat().st_mode&511) for p in k.rglob('*') if p.is_file()}
  assert replay[n]==expected
  assert all(n+'/'+rel in {x['name'] for x in v['files']} for rel in ('k/c.json','k/n.json','k/8.json','k/s.json'))
J.write(D/'EXTRA_TESTS.json',dict(status='PASS',environment_readonly=True,tree_readonly=True,root_writable=True,overlay_imported=True,full_hash_refusals=refusals,arming_full_replay=True))
print('EXTRA PASS: RO sites/tree; writable output; full-hash refusals; arming replay')
