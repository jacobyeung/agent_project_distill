"""Apply the delivered patch to a fresh authenticated copy and verify unchanged inputs."""
import ast,hashlib,json,os,subprocess
from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_reads228');W=L/'work/round4';K=W/'kit'
BASE=Path('/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A10b')
CPU='/scratch/jjyeung/envs/p1cpu/bin/python'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
manifest=read(K/'patches/MANIFEST.json');patch=K/'patches'/manifest['patch']['path'];fresh=W/'applied_release'
commands=[['nice','-n','10',CPU,'-I','-s','-B',str(K/'bootstrap228.py'),'--input-A10b',str(BASE),'--out',str(fresh)],
 ['nice','-n','10','patch','--batch','--fuzz=0','-p1','-d',str(fresh),'-i',str(patch)],
 ['nice','-n','10',CPU,'-I','-s','-B',str(fresh/'read228/bootstrap228.py'),'--input-A10b',str(fresh),'--out',str(fresh/'read228/A10b')]]
records=[]
for i,command in enumerate(commands):
 print(subprocess.check_output(['date','-u'],universal_newlines=True).strip(),flush=True)
 result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
 log=W/'checks'/('release_patch_command_'+str(i)+'.txt');log.write_text(result.stdout+result.stderr)
 records.append(dict(argv=command,returncode=result.returncode,output=log.name));assert result.returncode==0,result.stderr
 if i==1:assert 'fuzz' not in result.stdout and 'offset' not in result.stdout
for name,digest in manifest['files'].items():assert sha(K/name)==digest and sha(fresh/'read228'/name)==digest,name
pins=read(K/'A10b_PINS.json');original=[]
for name,spec in pins['source'].items():original.append(('src/'+name,spec['sha256']))
for name,spec in pins['package'].items():original.append(('package/'+name,spec['sha256']))
for name,spec in pins['operators'].items():original.append((name,spec['sha256']))
for name,digest in original:
 for root in (BASE,K/'A10b',fresh,fresh/'read228/A10b'):assert sha(root/name)==digest,(root,name)
old=read(L/'out_round3/DELIVERY_MANIFEST.json')
for name,spec in old['files'].items():assert sha(L/'out_round3'/name)==spec['sha256'],name
syntax=[]
for p in list(K.glob('*.py'))+list((K/'tests').glob('*.py')):ast.parse(p.read_text(),filename=str(p));syntax.append(str(p.relative_to(K)))
bootstrap=['common228.py','stage228.py','namespace228.py','inventory228.py','runtime228.py','runtime_registry228.py']
for name in bootstrap:ast.parse((K/name).read_text(),filename=name,feature_version=(3,6))
for p in list(K.glob('*.sh'))+[K/'tests/run_tests.sh']:
 result=subprocess.run(['nice','-n','10','bash','-n',str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert result.returncode==0,result.stderr
proof=dict(commands=records,patch_files=len(manifest['files']),patch_files_match=True,base_original_files_unchanged=len(original),
 round3_preserved_files=len(old['files']),python_syntax_files=syntax,python36_grammar_files=bootstrap,
 patch_sha256=sha(patch),git_calls=0,ssh_calls=0,gpu_runs=0)
(W/'checks/RELEASE_PATCH_INTEGRITY.json').write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in proof.items() if k not in ('commands','python_syntax_files')},sort_keys=True))
