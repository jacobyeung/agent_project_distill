"""Bind the proof to a fully derived, independently certified deployment."""
import argparse,hashlib,json,sys
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def validate_switches(cfg):
    """Admit only S2 with S1 off and both own-sampling probabilities zero."""
    h=cfg.get('h1',{})
    schedules=(cfg.get('scheduled_sampling',{}),cfg.get('recipe',{}).get('scheduled_sampling',{}))
    if (h.get('routing_pose_targets') is not True or h.get('faithful_own_camera_rows') is not False
            or any(type(s.get('max_own_probability')) not in (int,float)
                   or s['max_own_probability']!=0 for s in schedules)):
        raise ValueError('Launch requires S2=true, S1=false, and both max_own_probability=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('--kit',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--partition',choices=('advanced','general','bootstrap'),required=True)
    p.add_argument('--binding',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    binding=load(a.binding);launch=load(a.kit/'k/launch.json');cfg=load(a.kit/launch['config']['file'])
    sys.path.insert(0,str(a.kit/'b'));from i import identity
    from d import contract,digest
    if identity(cfg)!=binding['config_identity'] or launch['status']!='READY':raise ValueError('Final deployment identity/status differs')
    if sha(a.kit/launch['config']['file'])!=launch['config']['sha256']:raise ValueError('Config bytes differ')
    if cfg['s1_routing']['selection']['sha256']!=binding['selection_sha256']:raise ValueError('Selection differs')
    validate_switches(cfg)
    equality=load(a.kit/'k/selection_equality.json')
    if not equality.get('native_regeneration_executed') or equality.get('selection_sha256')!=binding['selection_sha256']:raise ValueError('Native selection regeneration required')
    if binding.get('unit_binding') and not equality.get('native_unit_regeneration_executed'):raise ValueError('Native unit selection regeneration required')
    allowed=['general','bootstrap'] if binding.get('continuation') else ['advanced','general','bootstrap']
    auth=load(a.kit/'k/4.json')
    if a.partition not in allowed or a.partition not in auth.get('allowed_partitions',[auth.get('partition')]):
        raise ValueError('Proof partition is not authorized')
    for directory in [a.kit/'b',*(p for p in (a.kit/'b').rglob('*') if p.is_dir())]:
        if directory.stat().st_mode & 0o777 != 0o500:raise ValueError('Kit code directory is not sealed')
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
    authority=dict(partition=a.partition,allowed_partitions=allowed,bundle_files=bundle_files,identity=identity(cfg),contract=digest(contract(launch,cfg)),kh=str(a.kit.resolve()),bun=str(a.bundle.resolve()),
        runtime=runtime,selection_sha256=binding['selection_sha256'],equality_sha256=sha(a.kit/'k/selection_equality.json'),
        wrapper_sha256=sha(a.bundle/'jb.sh'),persistent_root=launch['persistent_run_root'],job_name=binding['job_name'],
        run_key=binding['run_key'],tag=binding['run_key'])
    with a.out.open('x') as f:json.dump(authority,f,sort_keys=True,indent=2);f.write('\n')
if __name__=='__main__':main()
