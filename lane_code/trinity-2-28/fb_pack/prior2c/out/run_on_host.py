#!/usr/bin/env python3
"""Run the production checker on a final native proof root; never prepare or invent inputs."""
import argparse,hashlib,json,os,shlex,subprocess,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--proof-root',type=Path,required=True)
 p.add_argument('--stage',choices=('b','h','population'),default='b')
 p.add_argument('--base-tree',type=Path,required=True)
 p.add_argument('--patched-tree',type=Path,required=True)
 p.add_argument('--weights',type=Path,default=Path(__file__).with_name('TOWARD_HARD_WEIGHTS.json'))
 p.add_argument('--launch-config',type=Path,default=Path(__file__).with_name('N_LAUNCH_CONFIG.json'))
 p.add_argument('--output-dir',type=Path,required=True)
 p.add_argument('--pin',action='append',default=[],metavar='SHA256=PATH')
 a=p.parse_args();root=a.proof_root.resolve()/a.stage;out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 evidence={}
 def track(path):
  path=Path(path).resolve()
  if not path.is_file():raise FileNotFoundError('MISSING:'+str(path))
  h=hashlib.sha256()
  with path.open('rb') as f:
   for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
  evidence[str(path)]=dict(path=str(path),sha256=h.hexdigest());return path
 command=None
 try:
  checker=track(Path(__file__).with_name('prove_on_prepared.py'));track(__file__)
  config=track(root/'config.json');receipt=track(root/'receipt.json')
  cfg=json.loads(config.read_text());r=json.loads(receipt.read_text())
  if cfg.get('preparation',{}).get('sha256')!=evidence[str(receipt)]['sha256']:
   raise ValueError('PREPARATION_RECEIPT_HASH_MISMATCH:'+str(receipt))
  track(a.weights);track(a.launch_config)
  command=['nice','-n','10',sys.executable,str(checker),
   '--base-tree',str(a.base_tree.resolve()),'--patched-tree',str(a.patched_tree.resolve()),
   '--weights',str(a.weights.resolve()),'--launch-config',str(a.launch_config.resolve()),
   '--config',str(config),'--prepared-receipt',str(receipt),'--output-dir',str(out/'proof')]
  for stream in ('pose','vqa','routing','pointing'):
   v=r['streams'][stream];key='order' if v.get('kind')=='mix' else 'indices'
   command+=['--receipt',stream+'='+v['receipt']['path'],'--offset-table',stream+'='+v[key]['path']]
  for item in a.pin:command+=['--pin',item]
  result=dict(status='READY',command=shlex.join(command),inputs=list(evidence.values()))
 except Exception as exc:
  result=dict(status='MISSING' if 'MISSING:' in str(exc) else 'FAIL',error=type(exc).__name__+':'+str(exc),inputs=list(evidence.values()))
 with (out/'HOST_COMMAND.json').open('x') as f:f.write(json.dumps(result,sort_keys=True,indent=2)+'\n')
 if command is None or result['status']!='READY':print(result['error']);return 1
 print(result['command'],flush=True)
 env=dict(os.environ,OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',PYTHONDONTWRITEBYTECODE='1',
          CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 return subprocess.run(command,env=env).returncode

if __name__=='__main__':raise SystemExit(main())
