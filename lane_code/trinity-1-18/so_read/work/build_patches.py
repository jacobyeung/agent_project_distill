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
ROOTS=('b/e2e_reader','b/parity_kit','h1eval')
groups={
 '01_bounded_read_caches.diff':['u0/a0.py','u0/a1.py','u0/a2.py','u0/a3.py',
    'u0/tests/test_read_cache.py','u0/tests/test_off.py'],
 '02_atomic_scene_shards.diff':[f'u0/a{i}.py' for i in range(4,12)]+[
    'u0/tests/test_read_journal.py','u0/tests/test_public.py','u0/tests/test_round1.py',
    'u0/tests/test_compare.py','u0/tests/u0.json','u0/tests/u1.json']}

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
              default_off='all original files unchanged; no extension import/settings parse',
              activation='u0/a8.py --enable-extensions (apply BOTH patches)',patches={},unchanged_roots={})
original={}
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

run=L/'work/apply-round1'/uuid.uuid4().hex
verify=run/'src';verify.mkdir(parents=True)
copy_values(original,verify)

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
for rel,data in original.items():assert (verify/rel).read_bytes()==data,rel
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

suite=[]
env=dict(os.environ,READ_INPUT_SRC=str(A),READ_TEST_TMP=str(L/'work/test-artifacts'))
for name in ('read_cache','read_journal','off','public','round1','compare'):
 command=[sys.executable,'-I','-s','-B',str(verify/'u0/tests'/('test_'+name+'.py'))]
 result=subprocess.run(command,cwd=L,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 output='applied_'+name+'.txt';(L/'out/checks'/output).write_text(result.stdout)
 assert result.returncode==0,result.stdout
 suite.append(dict(name=name,returncode=0,command=command,output=output))
manifest['applied_cpu_suites']=suite
manifest['kit_files']={str(p.relative_to(L/'out/kit_parity50')):dict(sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
                       for p in sorted((L/'out/kit_parity50').iterdir()) if p.is_file()}
manifest['generated_utc']=datetime.now(timezone.utc).isoformat()
(L/'out/patches/MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
print('PASS: 2 additive unified diffs; '+str(len(all_files))+' files; zero-fuzz A4/B5 application; unchanged original hash trees.')
print('PASS: all 6 CPU suites pass from the fresh applied A4 tree.')
print('Applied verification root: '+str(run))
