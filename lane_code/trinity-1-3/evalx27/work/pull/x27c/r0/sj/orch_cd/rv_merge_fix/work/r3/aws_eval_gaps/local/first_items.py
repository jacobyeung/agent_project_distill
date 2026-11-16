"""CPU preflight for a sealed stage; reports absent real media without substituting fixtures."""
import argparse,hashlib,importlib.util,json,sys,tarfile
from pathlib import Path
from common import ROOT,sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',type=Path);p.add_argument('--output',type=Path,required=True)
p.add_argument('--mirror',type=Path);p.add_argument('--video-root');p.add_argument('--vsti-video-root');p.add_argument('--revsi-video-root');a=p.parse_args()
work=a.output.parent/('unpack_'+a.output.stem);work.mkdir(parents=True,exist_ok=True)
report={'stage':str(a.stage),'checks':{},'datasets':[]}
for line in (a.stage/'kit/SHA256SUMS.txt').read_text().splitlines():
 h,n=line.split('  ',1)
 if sha(a.stage/'kit'/n)!=h:raise ValueError('Sealed file changed: '+n)
for name,dest in [('0.tar','b'),('1.tar','q')]:
 with tarfile.open(a.stage/'kit/k'/name) as tf:
  tf.extractall(work/dest,filter='data')
boot_spec=importlib.util.spec_from_file_location('boot',a.stage/'kit/b/1.py');boot=importlib.util.module_from_spec(boot_spec);boot_spec.loader.exec_module(boot)
cfg=json.loads((work/'q/0.json').read_text());boot.resolve_inputs(cfg,work/'q')
report['checks']['inputs_resolved']=not any(str(v.get('path','')).startswith('$Q/') for d in cfg['datasets'] for v in d.values() if isinstance(v,dict))
if cfg.get('routing'):
 report['checks']['route_pin_resolved']=not cfg['routing']['table']['path'].startswith('$Q/')
report['model_inputs'] = {}
for name in {c['model'] for c in cfg['cells']} | {'base'}:
 model=cfg['models'][name];target=model['path']
 if a.mirror:
  target=str(a.mirror)+target.replace('/scratch/fsw/','/fsw/',1)
 entry={'path':target,'present':Path(target).exists()}
 if model.get('kind')=='c1_export' and Path(target).is_file():
  entry['artifact_sha_matches']=sha(target)==model['sha256']
 report['model_inputs'][name]=entry
report['checks']['model_inputs_present']=all(v['present'] and v.get('artifact_sha_matches',True) for v in report['model_inputs'].values())
for key in ('video_root','vsti_video_root','revsi_video_root'):
 if getattr(a,key):cfg['roots'][key]=getattr(a,key)
sys.path.insert(0,str(work/'b'))
from data import tasks_for
from cells import frame_count
from media import decode
from evalpath.official import build_prompt_context
for cell in cfg['cells']:
 for spec in cfg['datasets']:
  if spec['benchmark'] not in cell['benchmarks']:continue
  rows=tasks_for(spec,cfg['roots']);entry=dict(benchmark=spec['benchmark'],count=len(rows),frames=frame_count(cell),ends=[])
  for t in (rows[0],rows[-1]):
   item=dict(id=t['example_id'],video=t['video_path'],prompt_built=bool(build_prompt_context(t,'ours')))
   video=Path(t['video_path'])
   # Never let a metadata mapping turn this CPU preflight into an NFS video read.
   if not str(video.resolve()).startswith(('/scratch/','/dev/shm/')):
    item['decode_error']='Media path is not staged under /scratch or /dev/shm'
   elif not video.is_file():item['decode_error']='Run-node video is absent on this host'
   else:
    try:
     arrays,audit=decode(t,cell['layout'],frame_count(cell),cell.get('frame_set'))
     item.update(decoded_shape=list(arrays.shape),anchor_indices=audit['anchor_indices'])
    except Exception as e:item['decode_error']=f'{type(e).__name__}: {e}'
   entry['ends'].append(item)
  report['datasets'].append(entry)
report['pass']=all(report['checks'].values()) and all('decoded_shape' in t and t['prompt_built'] for d in report['datasets'] for t in d['ends'])
a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'report':str(a.output),'pass':report['pass'],'datasets':[(d['benchmark'],d['count']) for d in report['datasets']]}))
if not report['pass']:sys.exit(2)
