"""Check patch reproducibility, original-byte preservation, syntax, and workspace size."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round1';K=W/'kit'
def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
now=subprocess.check_output(['date','-u'],text=True).strip();print(now)
manifest=read(K/'patches/MANIFEST.json');patch=K/'patches'/manifest['patch']['path']
assert sha(patch)==manifest['patch']['sha256']
fresh=W/'patch_apply_proof';fresh.mkdir(exist_ok=False)
command=['nice','-n','10','patch','--batch','--fuzz=0','-p1','-d',str(fresh),'-i',str(patch)]
done=subprocess.run(command,capture_output=True,text=True)
(W/'checks/patch_apply_proof.txt').write_text(done.stdout+done.stderr)
assert done.returncode==0,done.stderr
assert 'fuzz' not in done.stdout and 'offset' not in done.stdout
for name,digest in manifest['files'].items():
    for base in (K,fresh/'read228',W/'applied_base/read228'):assert sha(base/name)==digest,(base,name)
pins=read(K/'A10b_PINS.json');original=[]
for name,spec in pins['source'].items():original.append(('src/'+name,spec['sha256']))
for name,spec in pins['package'].items():original.append(('package/'+name,spec['sha256']))
for name,spec in pins['operators'].items():original.append((name,spec['sha256']))
for name,digest in original:
    for base in (K/'A10b',W/'applied_base',W/'applied_base/read228/A10b'):assert sha(base/name)==digest,(base,name)
preserved=0
for path in (L/'out_round0').rglob('*'):
    if path.is_file():assert sha(path)==sha(L/'out'/path.relative_to(L/'out_round0'));preserved+=1
syntax=[]
for path in list(K.glob('*.py'))+list((K/'tests').glob('*.py')):
    ast.parse(path.read_text(),filename=str(path));syntax.append(str(path.relative_to(K)))
shell=['nice','-n','10','bash','-n']+[str(p) for p in K.glob('*.sh')]+[str(K/'tests/run_tests.sh')]
shell_result=subprocess.run(shell,capture_output=True,text=True);assert shell_result.returncode==0
size=0;count=0
for directory,dirs,names in os.walk(str(L),followlinks=False):
    for name in names:
        info=os.lstat(str(Path(directory)/name))
        if stat.S_ISREG(info.st_mode):size+=info.st_size;count+=1
assert size<3_000_000_000
result=dict(utc=now,patch_apply=dict(argv=command,returncode=done.returncode,added_files=len(manifest['files']),zero_fuzz=True),
    patch_files_match_tested_copy=True,base_original_files_unchanged=len(original),round0_preserved_files=preserved,
    python_syntax_files=syntax,shell_syntax=dict(argv=shell,returncode=shell_result.returncode),
    workspace_measured=dict(regular_file_bytes=size,regular_files=count,basis='sum of lstat sizes of regular files under L; excludes symlinks; no recursive traversal outside L'),
    actual_gpu_runs=0,ssh_calls=0,git_calls=0)
write(W/'checks/INTEGRITY.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('python_syntax_files','shell_syntax','patch_apply')},sort_keys=True))
