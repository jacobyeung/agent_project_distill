"""Allocation entry with inherited return transport and the neutral reader."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
from adapter import *
from venue import trinity_plan

def admit(family,assets):
    from engine import source_pins
    if family.get('schema')!='camera-read-family-v1':raise ValueError('family schema differs')
    if family.get('code_sources')!=source_pins():raise ValueError('packet code differs from sealed sources')
    if family['protocol']['served']!=['move','turn','pose'] or family['protocol']['arms']!=['native','scripted_camera']:
        raise ValueError('serving protocol differs')
    if family['limits']['full']['gpu_seconds']!=21600:raise ValueError('full allowance differs')
    bound=load(Path(assets['inputs'])/'BOUND.json')
    if bound['source_sha256']!=family['inputs']['item_sha256'] or bound['media_sha256']!=family['inputs']['media_sha256'] or bound['synthetic']:
        raise ValueError('bound input family differs')
    return bound

def run(config_path,assets_path,root):
    config=load(config_path);root=Path(root)
    if not os.environ.get('SLURM_JOB_ID','').isdigit():raise ValueError('assigned allocation required')
    if config['seconds']!=21600:raise ValueError('sealed full limit differs')
    family=load(checked(dict(path=str(Path(config_path).parent/config['family']['path']),sha256=config['family']['sha256'])))
    checked(dict(path=assets_path,sha256=config['assets']['sha256']))
    if family.get('schema')!='camera-read-family-v1':raise ValueError('family schema differs')
    assets=load(assets_path);admit(family,assets)
    import paths
    sys.path.extend([str(paths.CORE),str(paths.CORE/'orchard_native')])
    from native_job import card
    allocation=card(require_empty=True)
    plan=trinity_plan(root,assets,os.environ['CUDA_VISIBLE_DEVICES'],False,host_bwrap=False)
    dump(root/'ALLOCATION.json',allocation)
    if plan['missing']:raise ValueError('staged assets missing')
    # Orchard already owns an assigned card; vnice applies only to Trinity execution.
    command=plan['argv']+['job','--bound','/i/BOUND.json','--spec','/i/SPEC.json','--out','/r/cell','--limit','21600']
    started=time.monotonic();returncode=1
    with (root/'worker.log').open('w') as stream:
        result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        returncode=result.returncode
    returned=root/'return';returned.mkdir(exist_ok=False)
    source=root/'run/cell/j'
    for name in ('REQUEST.json','COMPLETE.json','CANARY.json','GPU_PARITY.json','items.jsonl'):
        p=source/name
        if p.is_file():
            target=returned/'cell/j'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
    g=root/'run/cell/g/scaled/GEOMETRY.json'
    if g.is_file():
        target=returned/'cell/g/scaled/GEOMETRY.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(g.read_bytes())
    complete=load(source/'COMPLETE.json') if (source/'COMPLETE.json').is_file() else {}
    if complete.get('reason')!='complete' or complete.get('missing'):returncode=returncode or 2
    dump(returned/'COMPLETE.json',dict(complete,plan_sha256=digest(config),synthetic=False,
                                      elapsed_seconds=time.monotonic()-started))
    import paths
    sys.path.insert(0,str(paths.CORE))
    import orchard_results
    return orchard_results.publish(returned,Path('/project/community/jjyeung/okh7/n2r'),config['token'],
                                   digest(config),returncode,synthetic=False,mode='full')

def main():
    p=argparse.ArgumentParser()
    for name in ('config','assets','root'):p.add_argument('--'+name,required=True)
    a=p.parse_args();run(a.config,a.assets,a.root)
if __name__=='__main__':main()
