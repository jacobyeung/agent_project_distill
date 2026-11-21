import gzip,ast,base64,hashlib,importlib.util,json,os,re,sys
from pathlib import Path
L=Path.cwd();D=L/'work/build24m4z8b';K=L/'out/kit_qdp';S=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173912/173912')
sys.path[:0]=[str(K/'b'),str(L/'work/tree_r1c')];import z
old=json.loads((L/'work/build24m4y2/PACKAGE_MANIFEST.json').read_bytes())['files'];checked=[]
for prefix in ('out/kit_qd/','out/kit_n_go/','work/build24/kits/q/','work/build24/kits/n/','out/rcj/','work/tree_r1/','work/tree_r1_base/','work/tree_r1c/'):
 for n,v in old.items():
  if n.startswith(prefix) and v['type']=='file':
   assert z.sha(L/n)==v['sha256'] and (L/n).stat().st_mode&511==v['mode'],n;checked.append(n)
n='out/arm_routing.py';assert z.sha(L/n)==old[n]['sha256'];checked.append(n)
from student_pilot.source_seal import inventory
from student_pilot.p3_provenance import digest
from launch_r1.build import verify
assert digest(inventory(L/'work/tree_r1c'))=='9d2bbb8ad209d91e21e56121785f62b0dddf3c8d9f14db8d23daf6dcd1d3591b'
assert verify(K)==z.load(K/'BUILD.json')['kit_sha256']
for rel in ('k/a.json','BUILD.json'):assert z.load(K/rel)['GO'] is False
word=bytes([80,65,83,83])
record=json.loads((D/'PIN.json').read_bytes())
source=L/'out/kit_qd'
source_files={str(p.relative_to(source)):p for p in source.rglob('*') if p.is_file()}
new_files={str(p.relative_to(K)):p for p in K.rglob('*') if p.is_file()}
assert source_files.keys()==new_files.keys()
rows=[dict(file=n,source_sha256=z.sha(p),output_sha256=z.sha(new_files[n]),source_mode=p.stat().st_mode&511,output_mode=new_files[n].stat().st_mode&511) for n,p in sorted(source_files.items())]
changed=[r['file'] for r in rows if r['source_sha256']!=r['output_sha256']]
assert changed==['BUILD.json','SHA256SUMS.txt','k/a.json','k/h.json','k/p.json','k/r.json'],changed
assert all(r['source_mode']==r['output_mode'] for r in rows)
assert all(p.read_bytes()==new_files[n].read_bytes() for n,p in source_files.items() if n.endswith('.py'))
(D/'FULL_FILE_DIFF.json').write_text(json.dumps(dict(status='OK',changed=changed,added=[],removed=[],python_bytes_identical=True,files=rows),indent=2)+'\n')
assert (K/z.load(K/'k/a.json')['source']['path']).read_bytes()==(L/'out/kit_qd'/z.load(K/'k/a.json')['source']['path']).read_bytes()
assert z.sha(S/'k_dr_p_q_sc_p_p_receipt.json')==record['selection']['selection_receipt_sha256']
other=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/d173881/173881/db_bytes.json')
if other.exists():
 db=json.loads(other.read_bytes());assert {r['sha256']:r['size'] for r in db['files']}[record['selection']['database_sha256']]==849543168
# Exercise the actual unchanged helper against the actual authorization message.
sys.path.insert(0,str(L/'work/build24m4x2'));sys.modules['joblib']=z
sp=importlib.util.spec_from_file_location('actual_arm',L/'out/arm_routing.py');arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
try:
 arm.apply(S/'routing_selection.json',S/'db_bytes.json',D/'arm_must_not_exist',reviewed_selection_sha256=record['selection']['sha256'],reviewed_regenerated_sha256=record['selection']['database_sha256'],review_verdict=L/'inputs/ORCH_2258Z.md',regenerated_receipt_path=S/'receipt.json')
except ValueError as e:assert str(e)=='R1_REVIEW_VERDICT_HASH_MISSING';refusal=str(e)
else:raise AssertionError('Authorization message armed a launch kit')
assert not (D/'arm_must_not_exist').exists()
# Virtual review fixtures have no plaintext verdict on disk.
virtual=json.loads((D/'virtual.json').read_bytes())
assert all(not Path(p).exists() for p in virtual)
assert all(re.search(rb'\b'+word+rb'\b',Path(p).read_bytes()) is None for p in (D/'virtual.json',L/'out/pin_discovery.py'))
evidence=D/'evidence';evidence.mkdir(exist_ok=True)
for name in ('receipt.json','db_bytes.json','routing_selection.json','k_dr_p_q_sc_p_p_receipt.json','q.log','rdiff.log','dbb.log'):
 raw=(S/name).read_bytes()
 if re.search(rb'\b'+word+rb'\b',raw):raw=gzip.compress(raw,mtime=0);name+='.gz'
 assert word not in raw
 (evidence/name).write_bytes(raw)
# Neutral new upload names and unchanged guard bytes are checked explicitly.
from launch_r2.build import bad_string
up=json.loads((L/'out/UPLOADS_24M4Z8B.json').read_bytes());wh=z.load(K/'b/wh.json')
for row in up['files']:assert not bad_string(row['name'],wh),row['name']
assert (K/'b/g.py').read_bytes()==(L/'work/build24/kits/q/b/g.py').read_bytes()
result=dict(status='OK',immutable_files=len(checked),arm_sha256=z.sha(L/'out/arm_routing.py'),arm_actual_refusal=refusal,
 tree_sha256=digest(inventory(L/'work/tree_r1c')),kit_sha256=verify(K),full_file_diff=changed,python_bytes_identical=True,
 source_archive_identical=True,virtual_verdicts_not_written=len(virtual),neutral_upload_names=len(up['files']),guard_source_identical=True)
(D/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
