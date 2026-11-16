"""Build deterministic draft objects; fail closed on unavailable upload metadata."""
import ast, base64, difflib, hashlib, io, json, os, sys, tarfile
from copy import deepcopy
from pathlib import Path
B=Path(__file__).resolve().parents[1]
W=B.parents[1]/'work'
S=B/'out/c8/sources'
R=S/'sj/orch_cd/evalx/work/milestone'
sys.path[:0]=[str(R/'orchard_native'),str(R)]
import native_launcher as L
import native_common as C

def dump(p,v):p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((W/'p9/metadata/FAMILY.json').read_text())
oldmask=json.loads((R/'orchard_native/MASK_CACHE_P6_BOUND.json').read_text())
mask=deepcopy(oldmask)
mask['producer_sha256']=sha(R/'native/out2/nomdg.py')
newmask=R/'orchard_native/MASK_CACHE_C8_BOUND.json'
if newmask.exists():
    assert json.loads(newmask.read_text())==mask
else:
    dump(newmask,mask)
dump(B/'out/MASK_REBIND_STATUS.json',dict(status='UNVERIFIED_DRAFT',
    generated_by='scalar producer pin replacement; actual cache-bind must reproduce this file',
    changed_fields=[k for k in mask if mask[k]!=oldmask.get(k)],
    producer_sha256=mask['producer_sha256'],cache_bind_executed=False,
    blocking_inputs=['masks.done','production Python environment']))

archive_path=B/'out/c8/code_c8.tar'
members={}
with tarfile.open(str(archive_path),'w',format=tarfile.USTAR_FORMAT) as archive:
    for p in sorted(S.rglob('*')):
        if not p.is_file():continue
        name=str(p.relative_to(S));data=p.read_bytes()
        info=tarfile.TarInfo(name)
        info.size=len(data);info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
        info.mode=0o755 if name.endswith(('/vnice/vnice.sh','/vnice/terminator.sh')) else 0o644
        p.chmod(info.mode)
        archive.addfile(info,io.BytesIO(data))
        members[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
oldmembers=next(x['members'] for x in old['assets']['small_objects'] if x['role']=='code')
assert set(members)==set(oldmembers)|{
    'sj/orch_cd/evalx/work/milestone/native/out2/gravity_guard.py',
    'sj/orch_cd/evalx/work/milestone/orchard_native/MASK_CACHE_C8_BOUND.json'}
assets=deepcopy(old['assets'])
newcode=next(x for x in assets['small_objects'] if x['role']=='code')
newcode.update(name=assets['cloud_prefix']+'/code_'+sha(archive_path)[:16]+'.tar',
    sha256=sha(archive_path),bytes=archive_path.stat().st_size,members=members,
    expanded_bytes=sum(x['bytes'] for x in members.values()),generation='0',md5='PENDING_UPLOAD')
assets['worker_entrypoint']['sha256']=sha(R/'orchard_native/native_worker.py')
contract=deepcopy(old['worker_contract'])
for p in list(contract['adapter_pins']):
    local=R/Path(p).relative_to(C.LOGICAL_ROOT)
    contract['adapter_pins'][p]=sha(local)
guard=str(C.LOGICAL_ROOT/'native/out2/gravity_guard.py')
contract['adapter_pins'][guard]=sha(R/'native/out2/gravity_guard.py')
contract['kernel_source_pins']={name:sha(R/'native/out2'/(name+'.py')) for name in ('nomdg','geometry')}
contract['mask_cache']=dict(path=str(C.LOGICAL_ROOT/'orchard_native/MASK_CACHE_C8_BOUND.json'),sha256=sha(newmask))
seal_path=B/'work/SEAL_NUMERIC_GENERATION_FIXTURE.json'
index=1
while seal_path.exists():
    seal_path=B/'work'/('SEAL_NUMERIC_GENERATION_FIXTURE_'+str(index)+'.json')
    index+=1
L.seal(assets,contract,seal_path)
family=json.loads(seal_path.read_text())
next(x for x in family['assets']['small_objects'] if x['role']=='code')['generation']='PENDING_UPLOAD'
dump(B/'out/c8/FAMILY_C8.json',family)

allowed_assets={'small_objects','worker_entrypoint'}
assert all(assets[k]==old['assets'][k] for k in assets if k not in allowed_assets)
assert all(p==q for p,q in zip(assets['small_objects'],old['assets']['small_objects']) if p['role']!='code')
assert all(contract[k]==old['worker_contract'][k] for k in contract
           if k not in ('adapter_pins','kernel_source_pins','mask_cache'))
assert family['limits']['full']==old['limits']['full']
assert {k:v for k,v in family['limits']['pilot'].items() if k!='gpu_seconds'}=={
    k:v for k,v in old['limits']['pilot'].items() if k!='gpu_seconds'}

patches=[];changed=[]
for p in sorted(S.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(S);prior=W/'code9'/rel
    before=prior.read_bytes() if prior.exists() else b''
    after=p.read_bytes()
    if before==after:continue
    changed.append(str(rel))
    patches.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
        fromfile='pilot9/'+str(rel) if prior.exists() else '/dev/null',tofile='c8/'+str(rel)))
for name in ('sj/orch_cd/evalx/work/camera/vnice/vnice.sh','sj/orch_cd/evalx/work/camera/vnice/terminator.sh'):
    patches.extend(['diff --git pilot9/'+name+' c8/'+name+'\n','old mode 100600\n','new mode 100755\n'])
(B/'out/C8_DIFF_vs_pilot9.patch').write_text(''.join(patches))
reasons={
 'gravity_guard.py':'Change 4 (0716Z, 0804Z): installs the reviewed predicate after sealed-source and terminal-AST checks, including exception-class identity.',
 'geometry.py':'Change 4 (0804Z): prepares each capture within its recorder context.',
 'perception.py':'Change 4 (0804Z): binds reloaded contracts to their capture before validation.',
 'nomdg.py':'Changes 3 and 4 (0510Z, 0645Z): records family probe selection and binds both guard identities in requests.',
 'native_worker.py':'Changes 1 and 4 (0454Z, 0948Z): records program refusals, installs the guard after restore, and reports checked guard dispositions.',
 'native_metrics.py':'Changes 1 and 4 (0454Z, 0948Z): excludes program refusals from token/timing checks and validates guard accounting.',
 'native_job.py':'Change 4 (0948Z): validates guard dispositions at pilot and full terminal admission; change 1 uses the corrected real projection.',
 'native_launcher.py':'Changes 2 and 4 plus packaging (0502Z, 0645Z): seals the pilot limit, packet guard identities, and both mask receipt pins.',
 'native_local_check.py':'Packaging for change 4: admits the new guard and new mask receipt in the explicit dependency sets; historical APPROVED remains unchanged.',
 'native_pin_graph.py':'Packaging: checks the new mask receipt path against the new reader producer pin.',
 'MASK_CACHE_C8_BOUND.json':'Packaging: draft producer-only rebind; cache-bind reproduction remains mandatory before admission.'}
(B/'out/DIFF_FILES.md').write_text('# Changed files\n\n'+'\n'.join(
    '- `'+name+'`: '+reasons[Path(name).name] for name in changed)+
    '\n- `camera/vnice/vnice.sh` and `camera/vnice/terminator.sh`: packaging sets executable archive modes; source bytes are unchanged.\n')
dump(B/'out/PACKAGE_STATUS.json',dict(status='DRAFT_NOT_ADMITTED',
    code_sha256=sha(archive_path),family_sha256=sha(B/'out/c8/FAMILY_C8.json'),
    diff_sha256=sha(B/'out/C8_DIFF_vs_pilot9.patch'),members=len(members),
    numeric_generation_fixture=str(seal_path),seal_function_executed=True,
    upload_fields=['assets.small_objects[role=code].generation','assets.small_objects[role=code].md5'],
    cache_bind_executed=False,whole_worker_rehearsal=False,
    note='The seal ran with generation 0 only in a local fixture; FAMILY_C8 contains required PENDING_UPLOAD fields and cannot pass cloud_uri until the operator fills them.'))
print(json.dumps(dict(code=sha(archive_path),family=sha(B/'out/c8/FAMILY_C8.json'),members=len(members))))
