"""Read native phase receipts without changing or rehashing their payloads."""
from pathlib import Path
import argparse,json,datetime
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('admission_directory')
p.add_argument('--launch-utc',help='ISO-8601 timestamp from launch p')
p.add_argument('--exit-utc',help='ISO-8601 timestamp from exit rc=0')
a=p.parse_args();root=Path(a.admission_directory).resolve()
def read(path):return json.loads(Path(path).read_text())
def stamp(path):return datetime.datetime.fromtimestamp(Path(path).stat().st_mtime,datetime.timezone.utc).isoformat()
results={};paths={}
for name in ('prepare','frames'):
 marker=read(root/f'phase_{name}.complete.json')
 path=Path(marker['payload']['path']);value=read(path)
 results[name]=dict(resources=value['resources'],result_path=str(path),result_mtime_utc=stamp(path))
 paths[name]=path.parent
prepared=read(paths['prepare']/'config.json')
frames=read(paths['frames']/'frames.json')
results['retained_sources']={k:{n:v[n] for n in ('rows','frame_references','unique_frames')} for k,v in frames['sources'].items()}
results['sum_frame_references']=sum(v['frame_references'] for v in frames['sources'].values())
results['fixed_samples']=sum(len(v['hash_sample']) for v in frames['sources'].values())
results['estimated_path_saving_seconds']=0.264*results['frames']['resources']['seconds']
results['estimate_basis']='0.264 times OFF phase_resources.frames.seconds; fixture extrapolation, possibly zero in production'
results['artifact_mtimes_utc']={}
for name in ('parent_grounding.json','pointing/receipt.json','vqa/receipt.json','routing/receipt.json','composed/receipt.json','prepared/receipt.json','config.json','result.json'):
 path=paths['prepare']/name
 if path.is_file():results['artifact_mtimes_utc'][name]=stamp(path)
if a.launch_utc and a.exit_utc:
 def dt(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
 total=(dt(a.exit_utc)-dt(a.launch_utc)).total_seconds()
 results['measured_modep_seconds']=total
 results['unattributed_seconds']=total-sum(results[k]['resources']['seconds'] for k in ('prepare','frames'))
results['notes']=['Native resources.seconds measure prepare and frames actions only.','Inter-phase mtime gaps are inferred and include receipt publication/hashing.','This diagnostic reads metadata and is not an authentication substitute.','Record the actual worker Python version and both switches from the launch environment separately.']
print(json.dumps(results,indent=2,sort_keys=True))
