"""Bind the proof to a fully derived, independently certified deployment."""
import argparse,hashlib,json,sys
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--kit',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--partition',choices=('advanced','general'),required=True)
    p.add_argument('--binding',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    binding=load(a.binding);launch=load(a.kit/'k/launch.json');cfg=load(a.kit/launch['config']['file'])
    sys.path.insert(0,str(a.kit/'b'));from i import identity
    from d import contract,digest
    if identity(cfg)!=binding['config_identity'] or launch['status']!='READY':raise ValueError('Final deployment identity/status differs')
    if sha(a.kit/launch['config']['file'])!=launch['config']['sha256']:raise ValueError('Config bytes differ')
    if cfg['s1_routing']['selection']['sha256']!=binding['selection_sha256']:raise ValueError('Selection differs')
    if cfg['h1']['routing_pose_targets'] or cfg['h1']['faithful_own_camera_rows']:raise ValueError('Launch switches must be off')
    equality=load(a.kit/'k/selection_equality.json')
    if not equality.get('native_regeneration_executed') or equality.get('selection_sha256')!=binding['selection_sha256']:raise ValueError('Native selection regeneration required')
    if binding.get('unit_binding') and not equality.get('native_unit_regeneration_executed'):raise ValueError('Native unit selection regeneration required')
    runtime={}
    for line in (a.kit/'SHA256SUMS.txt').read_text().splitlines():
        expected,name=line.split('  ',1)
        if name.startswith('b/') or name=='job.sh':
            if sha(a.kit/name)!=expected:raise ValueError('Runtime manifest differs')
            runtime[name]=expected
    bundle_files={}
    for line in (a.bundle/'sums.txt').read_text().splitlines():
        expected,name=line.split('  ',1)
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(a.bundle/name)!=expected:raise ValueError('Bundle bytes differ')
        bundle_files[name]=expected
    authority=dict(partition=a.partition,bundle_files=bundle_files,identity=identity(cfg),contract=digest(contract(launch,cfg)),kh=str(a.kit.resolve()),bun=str(a.bundle.resolve()),
        runtime=runtime,selection_sha256=binding['selection_sha256'],equality_sha256=sha(a.kit/'k/selection_equality.json'),
        wrapper_sha256=sha(a.bundle/'jb.sh'),persistent_root=launch['persistent_run_root'],job_name=binding['job_name'],
        run_key=binding['run_key'],tag=binding['run_key'])
    with a.out.open('x') as f:json.dump(authority,f,sort_keys=True,indent=2);f.write('\n')
if __name__=='__main__':main()
