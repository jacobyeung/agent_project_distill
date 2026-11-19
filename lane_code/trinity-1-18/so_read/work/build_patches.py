"""Build additive patches, prove unchanged originals, and test a fresh application."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import uuid
from datetime import datetime,timezone

L=Path('/scratch/jjyeung/orch_n30/so_read')
BASE=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3')
A=BASE/'A4/src';W=L/'work/src';E=W/'u0'
ROOTS=('b/e2e_reader','b/parity_kit','h1eval','orchard_h10')
groups={
 '01_bounded_read_caches.diff':['u0/a0.py','u0/a1.py','u0/a2.py','u0/a3.py',
    'u0/tests/test_read_cache.py','u0/tests/test_off.py'],
 '02_atomic_scene_shards.diff':[f'u0/a{i}.py' for i in range(4,12)]+[
    'u0/tests/test_read_journal.py','u0/tests/test_public.py','u0/tests/test_round1.py',
    'u0/tests/test_compare.py','u0/tests/u0.json','u0/tests/u1.json'],
 '03_production_integration.diff':[f'u0/a{i}.py' for i in range(12,21)]+['u0/tests/test_round2.py','u0/tests/test_round3.py',
     'u0/tests/test_operator_round3.py','u0/tests/test_lock_round3.py','u0/tests/test_round4.py','u0/tests/test_round5.py','u0/tests/test_round6.py','u0/tests/test_round7.py','u0/tests/test_round8.py']}

def sha(value):return hashlib.sha256(value).hexdigest()
def files(root):
 return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*')
         if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def tree_hash(values):
 return sha(json.dumps(sorted((k,sha(v)) for k,v in values.items()),sort_keys=True,
                       separators=(',',':'),ensure_ascii=False).encode())
def copy_values(values,root):
 for rel,data in values.items():
  path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

manifest=dict(base=str(A),strip=1,apply_from='fresh full staged src tree',
              default_off='all original reader files unchanged; no extension import/settings parse; operator additions conditional on read_extensions',
              activation='u0/a8.py --enable-extensions; u0/a19.py --enable-extensions builds the bound A4 cache-only package; a12 is the generic integration builder (apply reader patches 01-03 and A4 operator patches 04-05)',patches={},unchanged_roots={})
original={}
full_base=files(A)
manifest['base_pin']=dict(algorithm='sha256 of compact sorted JSON [relative_path, sha256] pairs',
                          sha256=tree_hash(full_base),files=len(full_base),
                          inventory={k:sha(v) for k,v in sorted(full_base.items())})
for rel in ROOTS:
 before=files(A/rel);after=files(W/rel)
 assert before==after,'Original hash tree changed: '+rel
 manifest['unchanged_roots'][rel]=dict(files=len(before),before_sha256=tree_hash(before),after_sha256=tree_hash(after))
 original.update({rel+'/'+k:v for k,v in before.items()})
for rel in ('rows/expected_calls.py','tree/student_pilot/h1_r0.py'):
 original[rel]=(A/rel).read_bytes()
all_files=[]
for name,paths in groups.items():
 parts=[];pins={}
 for rel in paths:
  assert not (A/rel).exists(),'Patches must be strictly additive'
  new=(W/rel).read_bytes()
  parts.extend(difflib.unified_diff([],new.decode().splitlines(True),fromfile='/dev/null',tofile='b/'+rel,n=3))
  pins[rel]=dict(before_sha256=None,after_sha256=sha(new),bytes=len(new));all_files.append(rel)
 raw=''.join(parts).encode();(L/'out/patches'/name).write_bytes(raw)
 manifest['patches'][name]=dict(sha256=sha(raw),bytes=len(raw),files=pins)

run=L/'work/apply-round8'/uuid.uuid4().hex
verify=run/'src';verify.mkdir(parents=True)
copy_values(full_base,verify)

def apply(root):
 outputs=[]
 for name in groups:
  with (L/'out/patches'/name).open('rb') as data:
   result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(root)],stdin=data,
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  assert result.returncode==0 and 'fuzz' not in result.stdout.lower(),result.stdout
  outputs.append(result.stdout)
 for rel in all_files:assert (root/rel).read_bytes()==(W/rel).read_bytes(),rel
 return ''.join(outputs)

application=apply(verify)
for rel,data in full_base.items():assert (verify/rel).read_bytes()==data,rel
b5=run/'b5/src';b5.mkdir(parents=True);b5_original={}
with tarfile.open(BASE/'B5/package/0.tgz','r:gz') as archive:
 for member in archive:
  rel=member.name.removeprefix('./')
  if member.isfile() and any(rel.startswith(prefix+'/') for prefix in ROOTS) and '__pycache__' not in rel and not rel.endswith('.pyc'):
   b5_original[rel]=archive.extractfile(member).read()
assert b5_original and 'h1eval/h10/launch.py' in b5_original
copy_values(b5_original,b5)
application+=apply(b5)
for rel,data in b5_original.items():assert (b5/rel).read_bytes()==data,rel
(L/'out/checks/patch_application.txt').write_text(application)
manifest['application_checks']=dict(A4='zero fuzz; all original files unchanged; added bytes exact',
                                   B5='zero fuzz; every extracted original file unchanged; added bytes exact')
manifest['verification_root']=str(run)


# The operator patch has a separate input root; the three reader patches are additive.
operator_before=(BASE/'A4/tower_sequence.py').read_bytes()
operator_after=(L/'work/operator4/tower_sequence.py').read_bytes()
assert operator_before==(L/'work/operator3-original/7.py').read_bytes()
name='04_operator_cache_bound.diff'
raw=''.join(difflib.unified_diff(operator_before.decode().splitlines(True),
    operator_after.decode().splitlines(True),fromfile='a/tower_sequence.py',tofile='b/tower_sequence.py',n=3)).encode()
(L/'out/patches'/name).write_bytes(raw)
operator_root=run/'operator';operator_root.mkdir()
(operator_root/'tower_sequence.py').write_bytes(operator_before)
result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(operator_root)],
                      input=raw,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
assert result.returncode==0 and b'fuzz' not in result.stdout.lower(),result.stdout
assert (operator_root/'tower_sequence.py').read_bytes()==operator_after
with (L/'out/checks/patch_application.txt').open('a') as f:f.write(result.stdout.decode())
manifest['patches'][name]=dict(sha256=sha(raw),bytes=len(raw),apply_from='fresh A4 operator directory, outside src',
    files={'tower_sequence.py':dict(before_sha256=sha(operator_before),after_sha256=sha(operator_after),bytes=len(operator_after))})
manifest['operator_base_pin']=dict(path=str(BASE/'A4/tower_sequence.py'),sha256=sha(operator_before),
    bootstrap_source=str(BASE/'A4/package/BATCH.sh'),batch_sha256=sha((BASE/'A4/package/BATCH.sh').read_bytes()),
    decoded_bootstrap_sha256=sha((L/'work/operator3-original/0.py').read_bytes()))
public_operator=L/'out/operator';public_operator.mkdir(exist_ok=True)
(public_operator/'0.py').write_bytes((L/'work/operator3-original/0.py').read_bytes())
(public_operator/'tower_sequence.py').write_bytes(operator_after)
# The return and CPU-proof helpers are A4 operator-side changes, guarded by
# read_extensions. They apply from the same operator directory as patch 04.
name='05_operator_return_and_proof.diff';parts=[];pins={}
for rel in ('unpack_return.py','package/a/5.py'):
 before=(BASE/'A4'/rel).read_bytes();after=(L/'work/operator4'/rel).read_bytes()
 parts.extend(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),
                                  fromfile='a/'+rel,tofile='b/'+rel,n=3))
 pins[rel]=dict(before_sha256=sha(before),after_sha256=sha(after),bytes=len(after))
 dest=operator_root/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(before)
 dest=public_operator/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(after)
raw=''.join(parts).encode();(L/'out/patches'/name).write_bytes(raw)
result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-d',str(operator_root)],input=raw,
                      stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
assert result.returncode==0 and b'fuzz' not in result.stdout.lower(),result.stdout
for rel in pins:assert sha((operator_root/rel).read_bytes())==pins[rel]['after_sha256']
with (L/'out/checks/patch_application.txt').open('a') as f:f.write(result.stdout.decode())
manifest['patches'][name]=dict(sha256=sha(raw),bytes=len(raw),files=pins,
    apply_from='fresh A4 operator directory, outside src, after patch 04')
manifest['operator_files']={str(p.relative_to(public_operator)):dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
    for p in public_operator.rglob('*') if p.is_file()}
manifest['application_checks']['A4_operator']='zero fuzz; explicit read_extensions default OFF; exact delivered bytes'

suite=[]
env=dict(os.environ,READ_INPUT_SRC=str(A),READ_TEST_TMP=str(L/'work/test-artifacts'),
         READ_OPERATOR_SOURCE=str(operator_root/'tower_sequence.py'),READ_OPERATOR4_SOURCE=str(operator_root))
manifest['a4_payload_pin']=dict(sha256=sha((BASE/'A4/package/0.tgz').read_bytes()),bytes=(BASE/'A4/package/0.tgz').stat().st_size)
manifest['a4_member_pins']={n:dict(sha256=sha((BASE/'A4'/n).read_bytes()),bytes=(BASE/'A4'/n).stat().st_size)
    for n in ('package/0.json','package/3.py','package/a/0.json','package/a/4.py','package/a/7.py','fetch_return.py')}
sys.path.insert(0,str(W/'u0'))
from a9 import pack
manifest['kit_files']={p.name:dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
    for p in (L/'out/kit_parity50').iterdir() if p.is_file()}
manifest['kit_files']['sample50.json']['public_sha256']=sha((json.dumps({'u0':pack(json.loads((L/'out/kit_parity50/sample50.json').read_bytes()))},sort_keys=True)+'\n').encode())
manifest['default_bound_export']=json.loads((L/'out/operations/DEFAULT_EXPORT_PROVENANCE.json').read_text())
(L/'out/patches/MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
for name in ('off','round4','round5','round6','round7','round8','compare'):
 command=[sys.executable,'-I','-s','-B',str(L/'work/run_fixture5.py'),str(verify/'u0/tests'/('test_'+name+'.py'))]
 result=subprocess.run(command,cwd=L,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 output='applied_'+name+'.txt';(L/'out/checks'/output).write_text(result.stdout)
 assert result.returncode==0,result.stdout
 suite.append(dict(name=name,returncode=0,command=command,output=output))
manifest['applied_cpu_suites']=suite
# Authenticate the actual 927-file roots, not only the small regression fixtures.
import importlib.util
sys.path[:0]=[str(L/'out/kit_parity50'),str(verify/'u0')]
spec=importlib.util.spec_from_file_location('verify_kit_roots',L/'out/kit_parity50/run.py')
kit=importlib.util.module_from_spec(spec);spec.loader.exec_module(kit)
kit.validate_roots(dict(original_source_root=str(A),source_root=str(verify)))
assert json.loads((L/'out/kit_parity50/BASE_PIN.json').read_bytes())==manifest['base_pin']
manifest['authenticated_roots']=dict(original=str(A),patched=str(verify),files_per_root=len(full_base))
manifest['kit_files']={str(p.relative_to(L/'out/kit_parity50')):dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
                       for p in sorted((L/'out/kit_parity50').iterdir()) if p.is_file()}
manifest['kit_files']['sample50.json']['public_sha256']=sha((json.dumps({'u0':pack(json.loads((L/'out/kit_parity50/sample50.json').read_bytes()))},sort_keys=True)+'\n').encode())
pins={rel:sha((W/rel).read_bytes()) for rel in sorted(all_files)}
assert pins==json.loads((L/'out/kit_parity50/EXTENSION_PINS.json').read_bytes())
manifest['b5_base_archive_sha256']=sha((BASE/'B5/package/0.tgz').read_bytes())
manifest['operations_files']={str(p.relative_to(L/'out/operations')):dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in (L/'out/operations').iterdir() if p.is_file()}
manifest['generated_utc']=datetime.now(timezone.utc).isoformat()
(L/'out/patches/MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('PASS: 3 additive reader diffs ('+str(len(all_files))+' files) plus 2 default-OFF A4 operator diffs; zero-fuzz application; unchanged original reader hash trees.')
print('PASS: OFF, round-4/5/6/7/8 integration and comparator suites pass from the fresh applied A4 tree; both complete 927-file base inventories authenticate.')
print('Applied verification root: '+str(run))

with (L/'work/STATUS.md').open('a') as f:
    f.write(subprocess.check_output(['date','-u'],text=True)+'Regenerated three additive reader diffs plus two operator diffs; full A4/B5/operator base pins, zero-fuzz application and applied-tree suites passed.\n')
