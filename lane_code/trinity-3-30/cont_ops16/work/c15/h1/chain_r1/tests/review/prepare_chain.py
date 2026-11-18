"""Create one fresh packet copy and run the four CPU cases once, outside the sandbox."""
import hashlib,json,os,shutil,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parents[2]
assert subprocess.check_output(['hostname','-s'],text=True).strip()=='trinity-1-3'
C=H/'chain_r1'
C.mkdir(mode=0o700)  # Existing results are never reused, removed or overwritten.
for name in ['build/tree','build/fx','runtime','tests/review']:
 shutil.copytree(H/name,C/name)
(C/'evidence/cpu').mkdir(parents=True)
(C/'logs').mkdir()
for name in ['ids.json','UPLOAD.json']:shutil.copyfile(H/name,C/name)
pins={}
for name in ['build/tree','build/fx','runtime','tests/review']:
 for src in sorted((H/name).rglob('*')):
  if src.is_file():
   rel=src.relative_to(H);want=hashlib.sha256(src.read_bytes()).hexdigest()
   assert hashlib.sha256((C/rel).read_bytes()).hexdigest()==want
   pins[str(rel)]=want
(C/'input_hashes.json').write_text(json.dumps(pins,indent=2)+'\n')
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
summary=[];blocked=False
for case in ['signal','fileonly','hfail','full200']:
 out=C/'evidence/cpu'/case
 script='rv_run_chain_hfail.py' if case=='hfail' else 'rv_run_chain.py'
 rc=None;error=None
 if blocked:error='Not started after an earlier harness failure; inspect the retained process and logs before any rerun.'
 else:
  with (C/'logs'/(case+'.log')).open('x') as log:
   try:rc=subprocess.run([sys.executable,'-B',str(C/'tests/review'/script),case],env=env,cwd=C,stdout=log,stderr=subprocess.STDOUT,timeout=900).returncode
   except subprocess.TimeoutExpired:error='Harness timed out; inspect remaining children; no relaunch.'
 result=out/'result.json'
 if rc==0 and result.exists():
  data=json.loads(result.read_text());data['status']='PASS'
 else:
  data=dict(case=case,status='FAIL',exit=rc,error=error or 'Harness failed; see logs/'+case+'.log')
  blocked=True
 out.mkdir(parents=True,exist_ok=True)
 result.write_text(json.dumps(data,indent=2)+'\n')
 line=f"{data['status']} {case} {result.relative_to(H)}"
 print(line,flush=True);summary.append(line)
(C/'summary.txt').write_text('\n'.join(summary)+'\n')
sys.exit(1 if blocked else 0)
