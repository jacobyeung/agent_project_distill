"""Seal the exact source bytes and deterministic archive using the production sealer."""
import ast,base64,difflib,hashlib,io,json,sys,tarfile,uuid
from pathlib import Path
from copy import deepcopy
B=Path(__file__).resolve().parents[1];W=B.parents[1]/'work'
S=B/'out/c8r/sources';R=S/'sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(R/'orchard_native'),str(R)]
import native_launcher as L
import native_common as C
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
old=load(B.parent/'01_c8/out/c8/FAMILY_C8.json')
receipt=R/'orchard_native/MASK_CACHE_C8_BOUND.json'
rebound=B.parent/'01_c8/work/rh_pilot_06/MASK_CACHE_REBOUND.json'
assert receipt.read_bytes()==rebound.read_bytes()
assert sha(receipt).startswith('3be02a82')
assert load(receipt)['producer_sha256']==sha(R/'native/out2/nomdg.py')
archive=B/'out/c8r/code_c8r.tar';members={}
with tarfile.open(archive,'w',format=tarfile.USTAR_FORMAT) as tf:
 for p in sorted(S.rglob('*')):
  if not p.is_file():continue
  name=str(p.relative_to(S));data=p.read_bytes()
  if p.suffix=='.py':ast.parse(data,filename=str(p))
  info=tarfile.TarInfo(name);info.size=len(data);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
  info.mode=0o755 if name.endswith(('/vnice/vnice.sh','/vnice/terminator.sh')) else 0o644
  p.chmod(info.mode);tf.addfile(info,io.BytesIO(data))
  members[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
assert set(members)==set(next(x for x in old['assets']['small_objects'] if x['role']=='code')['members'])
assets=deepcopy(old['assets']);part=next(x for x in assets['small_objects'] if x['role']=='code')
part.update(name=assets['cloud_prefix']+'/code_'+sha(archive)[:16]+'.tar',sha256=sha(archive),
 bytes=archive.stat().st_size,members=members,expanded_bytes=sum(x['bytes'] for x in members.values()),
 generation='0',md5='PENDING_UPLOAD')
assets['worker_entrypoint']['sha256']=sha(R/'orchard_native/native_worker.py')
contract=deepcopy(old['worker_contract'])
for path in contract['adapter_pins']:
 contract['adapter_pins'][path]=sha(R/Path(path).relative_to(C.LOGICAL_ROOT))
contract['kernel_source_pins']={name:sha(R/'native/out2'/(name+'.py')) for name in ('nomdg','geometry')}
contract['mask_cache']['sha256']=sha(receipt)
fixture=B/'work'/('SEAL_FIXTURE_'+uuid.uuid4().hex+'.json')
L.seal(assets,contract,fixture)
family=load(fixture)
next(x for x in family['assets']['small_objects'] if x['role']=='code')['generation']='PENDING_UPLOAD'
dump(B/'out/c8r/FAMILY_C8R.json',family)
assert all(v==old['assets'][k] for k,v in assets.items() if k not in ('small_objects','worker_entrypoint'))
assert all(p==q for p,q in zip(assets['small_objects'],old['assets']['small_objects']) if p['role']!='code')
assert all(v==old['worker_contract'][k] for k,v in contract.items() if k!='mask_cache')
assert family['limits']['pilot']['gpu_seconds']==6000
assert family['limits']['full']['gpu_seconds']==21600
changed={};changed_lines={}
for label,prior in [('C8',B.parent/'01_c8/out/c8/sources'),('pilot9',W/'code9')]:
 patches=[];names=[]
 for p in sorted(S.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(S);before=prior/rel
  raw_a=before.read_bytes() if before.exists() else b'';raw_b=p.read_bytes()
  if raw_a==raw_b:continue
  a=raw_a.decode();b=raw_b.decode()
  names.append(str(rel))
  patches.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),
       fromfile=label+'/'+str(rel) if before.exists() else '/dev/null',tofile='c8r/'+str(rel)))
  if p.suffix=='.py':
   lines=set()
   for tag,i,j,k,l in difflib.SequenceMatcher(None,a.splitlines(),b.splitlines(),autojunk=False).get_opcodes():
    if tag in ('insert','replace'):lines.update(range(k+1,l+1))
   changed_lines.setdefault(str(rel),{})[label]=sorted(lines)
 if label=='pilot9':
  for name in ('vnice.sh','terminator.sh'):
   member='sj/orch_cd/evalx/work/camera/vnice/'+name
   patches+=['diff --git pilot9/'+member+' c8r/'+member+'\n','old mode 100600\n','new mode 100755\n']
 (B/'out'/('C8R_DIFF_vs_'+label+'.patch')).write_text(''.join(patches));changed[label]=names
dump(B/'out/CHANGED_LINES.json',changed_lines)
reasons={
 'orchard_results.py':'C8r change 1: publishes bounded independent pool/GCS returns, verifies readback, probes pool writes, and fetches either channel.',
 'orchard_launcher.py':'C8r change 1: delegates fetching to the authenticated dual-channel return API.',
 'native_job.py':'C8 changes 1 and 4 preserve terminal refusal/guard checks; C8r change 1 probes the pool before staging and supplies mode and family cloud configuration.',
 'native_launcher.py':'C8 changes 2 and 4 seal limits and guard identities; C8r changes 1, 2 and 4 seal return caps, the exact receipt, and the changed direct-launcher digest.',
 'native_metrics.py':'C8 changes 1 and 4 validate refusals and guard accounting; C8r change 1 projects against the full return cap.',
 'native_local_check.py':'C8 change 4 admits the guard dependency; C8r changes 1 and 4 admit the two changed transport sources in the explicit packaging set.',
 'MASK_CACHE_C8_BOUND.json':'C8r change 2 ships the exact cache-bind output bytes.',
 'native_pin_graph.py':'C8 change 4 and packaging bind the new mask receipt path.',
 'native_worker.py':'C8 changes 1 and 4 count program refusals and install and report the authenticated gravity guard.',
 'nomdg.py':'C8 changes 3 and 4 select a present-family parity probe and bind guard identities.',
 'gravity_guard.py':'C8 change 4 authenticates and wraps the sealed geometry validator.',
 'geometry.py':'C8 change 4 prepares captures within their guard recording context.',
 'perception.py':'C8 change 4 binds reloaded geometry contracts to capture contexts.'}
(B/'out/DIFF_FILES.md').write_text('# Changed files\n\n'+'\n'.join('- `'+n+'`: '+reasons[Path(n).name] for n in changed['pilot9'])+
 '\n- `camera/vnice/vnice.sh` and `camera/vnice/terminator.sh`: C8 packaging preserves executable archive modes.\n'
 '- `out/rehearsal/run_rehearsal.py`: C8r change 3 retains real single-process execution and refuses unsupported sharding; C8r change 1 exercises the new return API.\n'
 '- `out/rehearsal/cpu_boundary.py`: C8r changes 2 and 4 select the new family and require byte-exact cache-bind reproduction.\n')
result=dict(code_sha256=sha(archive),family_sha256=sha(B/'out/c8r/FAMILY_C8R.json'),
 diffs={label:sha(B/'out'/('C8R_DIFF_vs_'+label+'.patch')) for label in changed},members=len(members),
 receipt_sha256=sha(receipt),seal_executed=True,
 pending_upload=['assets.small_objects[role=code].generation','assets.small_objects[role=code].md5'])
dump(B/'out/PACKAGE_STATUS.json',result);print(json.dumps(result))
