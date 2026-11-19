"""Bootstrap, apply, and authenticate a fresh standalone copy of the delivered patch."""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round2';K=W/'kit'
BASE=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A10b')
CPU='/scratch/jjyeung/envs/p1cpu/bin/python'
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
fresh=W/'applied_verified'
commands=[['nice','-n','10',CPU,'-I','-s','-B',str(K/'bootstrap228.py'),'--input-A10b',str(BASE),'--out',str(fresh)],
          ['nice','-n','10','patch','--batch','--fuzz=0','-p1','-d',str(fresh),'-i',str(patch)],
          ['nice','-n','10',CPU,'-I','-s','-B',str(fresh/'read228/bootstrap228.py'),'--input-A10b',str(fresh),'--out',str(fresh/'read228/A10b')]]
record=[]
for index,command in enumerate(commands):
    print(subprocess.check_output(['date','-u'],text=True).strip(),flush=True)
    result=subprocess.run(command,capture_output=True,text=True)
    output=W/'checks'/('patch_command_'+str(index)+'.txt');output.write_text(result.stdout+result.stderr)
    record.append(dict(argv=command,returncode=result.returncode,output=str(output)))
    assert result.returncode==0,result.stdout+result.stderr
    if index==1:assert 'fuzz' not in result.stdout and 'offset' not in result.stdout
for name,digest in manifest['files'].items():
    assert sha(K/name)==digest and sha(fresh/'read228'/name)==digest,name
pins=read(K/'A10b_PINS.json');original=[]
for name,spec in pins['source'].items():original.append(('src/'+name,spec['sha256']))
for name,spec in pins['package'].items():original.append(('package/'+name,spec['sha256']))
for name,spec in pins['operators'].items():original.append((name,spec['sha256']))
for name,digest in original:
    for root in (BASE,K/'A10b',fresh,fresh/'read228/A10b'):assert sha(root/name)==digest,(root,name)
preserved=0
for path in (L/'out_round1').rglob('*'):
    if path.is_file():assert sha(path)==sha(L/'out'/path.relative_to(L/'out_round1'));preserved+=1
syntax=[]
for path in list(K.glob('*.py'))+list((K/'tests').glob('*.py')):
    ast.parse(path.read_text(),filename=str(path));syntax.append(str(path.relative_to(K)))
bootstrap=['common228.py','stage228.py','runtime228.py','inventory228.py','namespace228.py']
for name in bootstrap:ast.parse((K/name).read_text(),filename=name,feature_version=(3,6))
shell=[]
for path in list(K.glob('*.sh'))+[K/'tests/run_tests.sh']:
    result=subprocess.run(['nice','-n','10','bash','-n',str(path)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr;shell.append(str(path.relative_to(K)))
size=0;count=0
for directory,dirs,names in os.walk(str(L),followlinks=False):
    for name in names:
        info=os.lstat(str(Path(directory)/name))
        if stat.S_ISREG(info.st_mode):size+=info.st_size;count+=1
assert size<3_000_000_000
value=dict(utc=now,commands=record,patch_files_match=True,patch_files=len(manifest['files']),
    base_original_files_unchanged=len(original),round1_preserved_files=preserved,
    python_syntax_files=syntax,python36_grammar_files=bootstrap,shell_syntax_files=shell,
    workspace_regular_file_bytes=size,workspace_regular_files=count,actual_gpu_runs=0,ssh_calls=0,git_calls=0)
write(W/'checks/PATCH_INTEGRITY.json',value)
print(json.dumps(value,sort_keys=True))
