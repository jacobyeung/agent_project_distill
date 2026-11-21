"""Produce native scene evidence in the future authenticated job namespace."""
from pathlib import Path
from copy import deepcopy
import subprocess
import os
import sys
import time

def bind(cfg, sources, scratch, destination, kit, routing_base=None,pool_inputs=None):
    import student_pilot
    from student_pilot.p3_provenance import load, pinned
    from student_pilot.r1_persisted import scope
    from z import write, sha
    scratch,destination,kit=Path(scratch),Path(destination),Path(kit)
    # The loaded package is authoritative: discovery can override the shell path.
    trainer=Path(student_pilot.__file__).resolve().parent.parent
    inputs={trainer,scratch,kit/'b',Path(__file__).resolve().parent}
    inputs.update(Path(p) for p in sources.values())
    inputs.update(Path(p) for p in os.environ.get('PYTHONPATH','').split(os.pathsep) if p)
    if os.environ.get('ANYHOST_JOBS'):inputs.add(Path(os.environ['ANYHOST_JOBS']))
    inputs={p.absolute() for p in inputs}
    for path in sorted(inputs):
        if not path.exists():raise ValueError('R1_SCENE_BIND_SOURCE_MISSING:'+str(path))
    # Keep both logical aliases and their targets available after replacing /tmp.
    inputs.update(p.resolve() for p in tuple(inputs))
    effective=deepcopy(cfg)
    if routing_base is not None:effective['streams']['routing']=routing_base
    with scope(sources):
        from student_pilot.r2_scene_bindings import SOURCES
        pose=load(pinned(effective['streams']['pose']))
        if len(pose['sources'])!=2:raise ValueError('R1_SCENE_SOURCE_COUNT_DIFFERS')
        pins={name:(pose['sources'][0 if name=='pose_a2v3' else 1]['receipt']
                    if stream=='pose' else effective['streams'][stream]) for name,stream in SOURCES.items()}
        rows={}
        for name,pin in pins.items():
            receipt=load(pinned(pin))
            rows[name]=dict(receipt=pin,rows=receipt.get('rows_metadata',receipt.get('database')),count=receipt['count'])
            if rows[name]['rows'] is None:raise ValueError('R1_SCENE_SOURCE_POPULATION_MISSING:'+name)
            pinned(rows[name]['rows'])
        pool=load(pinned(effective['s1_routing']['selection']))
        original=pool_inputs or pool
        spec=dict(sources=rows,pool_manifest=original['manifest'],remove_files=cfg['remove_files'],tokenizer=original.get('tokenizer'))
        pinned(spec['pool_manifest'])
    physical=scratch/'sc';physical.mkdir(mode=0o700)
    control=scratch/'sc.json'
    write(control,dict(config=effective,spec=spec,paths=sources,output=str(destination/'sc')))
    parent=destination.parent
    import shutil
    binary=shutil.which('bwrap')
    if not binary:raise ValueError('R1_BINARY_MISSING:bwrap')
    # Build a fresh root so covering /tmp cannot hide a bind source.
    command=[binary]
    for name in sorted(os.listdir('/')):
        if name in ('tmp','proc','dev'):continue
        path='/'+name
        if os.path.islink(path):command+=['--symlink',os.readlink(path),path]
        elif os.path.isdir(path):command+=['--ro-bind',path,path]
    command+=['--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp']
    for path in sorted(inputs,key=lambda p:(len(p.parts),str(p))):
        command+=['--ro-bind',str(path),str(path)]
    command+=['--bind',str(physical),str(destination),'--remount-ro','/tmp','--remount-ro','/',
              '--chdir',str(parent),sys.executable,'-B','-s',str(Path(__file__).resolve()),str(control),str(trainer)]
    start=time.monotonic()
    try:subprocess.run(command,check=True)
    finally:print('scene rebuild seconds=%.3f'%(time.monotonic()-start),flush=True)
    physical=physical/'sc';result=load(physical/'2.json')
    cfg['r2_scene_rebuild']=dict(path=str(destination/'sc/2.json'),sha256=sha(physical/'2.json'))
    cfg['scene_coverage']=result['scene_coverage']
    cfg['s1_routing']['selection']=result['pool_selection']
    return physical

def main():
    sys.path.insert(0,sys.argv[2])
    from student_pilot.p3_provenance import load,file_pin
    from student_pilot.r1_persisted import scope
    from student_pilot.r2_scene_bindings import rebuild,verify
    value=load(sys.argv[1])
    with scope(value['paths']):
        result=rebuild(value['spec'],value['config'],value['output'])
        cfg=dict(value['config'],r2_scene_rebuild=file_pin(Path(value['output'])/'2.json'),scene_coverage=result['scene_coverage'])
        verify(cfg)

if __name__=='__main__':main()
