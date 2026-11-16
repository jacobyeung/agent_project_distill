"""Stage C8r's proof export and the plan-bound candidate in one private root."""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from guard_core import read,write,sha,verify_archive
from guard_backend import CORE
from closure import ROOT,unpack

def reject_hardlinks(stream):
    position=stream.tell()
    try:
        with tarfile.open(fileobj=stream,mode='r:*') as archive:
            if any(member.islnk() for member in archive):
                raise ValueError('Input archive contains a hard link; regularize it before review')
    finally:stream.seek(position)


def stage(root,config,payload):
    sys.path[:0]=[str(CORE/'orchard_native'),str(CORE)]
    import native_stage as S
    import orchard_job as J
    original_extract=S.S.extract_stream
    def extract_checked(stream,*args,**kwargs):
        reject_hardlinks(stream)
        return original_extract(stream,*args,**kwargs)
    S.S.extract_stream=extract_checked
    root,payload=Path(root),Path(payload)
    baseline=read(payload/'inputs/BASELINE_CONFIG.json')
    # These are operational copies with exactly the sealed source bytes.
    for key,value in config.get('asset_copies',{}).items():
        old,new=key,value
        def replace(v):
            if isinstance(v,str):return new if v==old else v
            if isinstance(v,list):return [replace(x) for x in v]
            if isinstance(v,dict):return {k:replace(x) for k,x in v.items()}
            return v
        baseline['assets']=replace(baseline['assets'])
    proof=deepcopy(baseline)
    proof['logical_run']='/scratch/jjyeung/orch_cd/evalx/work/milestone/runs/'+config['token']
    # The unchanged stage authenticates all shared assets and the historical export.
    records=S.stage(root,proof)
    S.physical(root,proof['logical_run']).mkdir(parents=True,exist_ok=False)
    desc=read(payload/'CLOSURE.json');desc['archive']['path']=str(payload/'metadata.tar')
    files=unpack(desc,root/'candidate_metadata')
    artname=f'runs/359fcc3c/m{config["step"]}/artifact.json'
    for name,raw in files.items():
        # The export stager exclusively creates its own milestone directory.
        if name.startswith('runs/359fcc3c/m') and '/artifact.json' in name:continue
        target=S.physical(root,ROOT+name);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():
            if target.read_bytes()!=raw:raise ValueError('Candidate metadata collides with a shared pin')
        else:target.write_bytes(raw)
    done=root/'candidate.done';done.write_bytes((payload/'candidate.done').read_bytes())
    export=root/'archives/candidate.tar';expected=config['done']
    env=S.S.cloud_environment(baseline['assets']['gcloud_config'])
    count=0
    with export.open('xb') as output:
        for index in range(4):
            name=expected['object']+f'.part{index:02d}-of-04'
            with S.S.process_stream(['/usr/bin/gcloud','storage','cat','gs://cmu-gpucloud-jjyeung/'+name],env,root/'candidate_stage.log') as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b''):
                    count+=len(chunk)
                    if count>expected['bytes']:raise ValueError('Candidate export exceeds its done bytes')
                    output.write(chunk)
    verify_archive(export,expected)
    model=read(S.physical(root,baseline['assets']['model_manifest']['path']))
    runtime=records['runtime_spec']
    checker=dict(namespace=S.namespace(root,proof),python=runtime['python']['path'],
                 base=model['root'],environment=J.environment(root))
    req=dict(root=str(root),archive=str(export),done=str(done),step=config['step'],expected=expected,checker=checker)
    write(root/'candidate_stage_request.json',req)
    subprocess.run([sys.executable,'-I','-s','-B',str(Path(__file__).parent/'stage_candidate.py'),
                    '--request',str(root/'candidate_stage_request.json')],check=True,env=env)
    artifact=S.physical(root,ROOT+artname)
    if artifact.read_bytes()!=files[artname]:raise ValueError('Export and closure artifacts differ byte-for-byte')
    worker=dict(baseline=baseline,step=config['step'],candidate={
        **{k:desc['admission'][k] for k in ('config','data_receipt')},
        'artifact':dict(path=ROOT+artname,sha256=sha(artifact))},
        reference=dict(path=str(payload/'inputs/reference.json'),sha256=sha(payload/'inputs/reference.json')),
        items=dict(path=str(payload/'inputs/items.json'),sha256=sha(payload/'inputs/items.json')),
        closure_root=str(root/'candidate_metadata'),closure_names=sorted(files))
    write(root/'WORKER.json',worker)
    return proof,records
