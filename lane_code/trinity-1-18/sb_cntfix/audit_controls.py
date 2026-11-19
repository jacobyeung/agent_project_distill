"""CPU-only negative test of completion-marker validation; no GPU or process control."""
from pathlib import Path
import hashlib,json,subprocess,os,sys
root=Path(__file__).resolve().parent
manifest=root/'out/MANIFEST_R0DEV.json'; mh=hashlib.sha256(manifest.read_bytes()).hexdigest();m=json.loads(manifest.read_text())
runner=root/'kit/files/run_count_teacher.py'
inputs={str(manifest):mh,str(runner):hashlib.sha256(runner.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
bad=root/'out/resume_invalid';bad.mkdir(exist_ok=True)
for c in m['captures']:
 d=bad/c['canonical'].replace('/','__');d.mkdir(exist_ok=True)
 p=d/'DONE.json';p.write_text(json.dumps({'test':'Intentionally invalid completion marker; no teacher output exists.','inputs_sha256':inputs})+'\n')
 inputs_marker=hashlib.sha256(p.read_bytes()).hexdigest()
cmd=['/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python',str(runner),'--manifest',str(manifest),'--manifest-sha256',mh,'--out',str(bad),'--stub','--hours','0']
r=subprocess.run(cmd,cwd='/scratch/jjyeung/orch_n30/b05_owngrd/code',env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,universal_newlines=True)
result=dict(inputs_sha256=inputs,command=cmd,returncode=r.returncode,stdout=r.stdout,invalid_markers=len(m['captures']),teacher_outputs=len(list(bad.glob('*/teacher.json.gz'))),journal=(bad/'PROGRESS.0of1.jsonl').read_text())
for p in sorted(bad.glob('*/DONE.json')):result['inputs_sha256'][str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'out/CONTROL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print('Invalid resume test:',r.returncode,'exit;',result['invalid_markers'],'invalid DONE markers;',result['teacher_outputs'],'teacher outputs;',result['journal'].strip())
