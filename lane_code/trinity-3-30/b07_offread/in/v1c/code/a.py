"""Allocation phases with stable logical paths for a resumable read."""
import argparse
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from adapter import *
from budget import DEFAULT,Budget


def phase(root,name,start):
    p=Path(root)/'PHASES.json';value=load(p) if p.exists() else []
    value.append(dict(name=name,seconds=time.monotonic()-start,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))
    dump(p,value)


def run(config_path,deadline_utc=DEFAULT,command='read'):
    config=load(config_path);root=Path('/r');spec=load('/d/s.json');budget=Budget(deadline_utc)
    start=time.monotonic();resume=config.get('resume',[])
    import engine
    engine.initialize(spec)
    if command=='prepare':
        if not resume:
            prepare('/d/c.json','/d/d.json','/b/frames',root/'i')
        else:
            prepare('/d/c.json','/d/d.json','/b/frames',root/'v')
            fresh=relocate_input(root/'v','/r/i')
            if fresh!=load(root/'i/BOUND.json'):raise ValueError('resumed frame/input pins differ')
            (root/'v/store').rename(root/'i/store')
        bound=validate_bound(root/'i/BOUND.json')
        if len(bound['keys'])!=450 or len(load(checked(bound['inputs']['FRAMES.json']))['captures'])!=311:
            raise ValueError('read membership differs')
        phase(root,'stage',start)
        if not resume:
            start=time.monotonic();raw=engine.tower(bound,spec,root/'cell/g/raw');phase(root,'pose',start)
            start=time.monotonic();boundary=engine.NativeBoundary(spec)
            engine.prepare_geometry(bound,spec,raw,root/'cell/g/scaled',boundary);phase(root,'prepare',start)
        return
    geometry=root/'cell/g/scaled/GEOMETRY.json';proof_path=root/'p/PROOF.json'
    if resume:proof_path=checked(load(Path(resume[0])/'COMPLETE.json')['proof'])
    start=time.monotonic();boundary=engine.NativeBoundary(spec);out=root/config['segment']
    value=engine.run(root/'i/BOUND.json',spec,geometry,out,boundary=boundary,
        limit=min(21600,max(1e-9,budget.remaining())),deadline_utc=deadline_utc,resume=resume,proof_path=proof_path)
    phase(root,'read',start)
    merged=engine.merge(root/'i/BOUND.json',resume+[str(out)],root/'MERGED.json',partial=True)
    # The operator builds the named comparison report locally from the returned journals.
    dump(root/'RESULT.json',dict(complete=merged['complete'],missing=merged['missing'],segment=config['segment'],deadline=deadline_utc))
    return value


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--deadline-utc',default=DEFAULT)
    p.add_argument('--phase',choices=('prepare','read'),default='read')
    a=p.parse_args();run(a.config,a.deadline_utc,a.phase)
if __name__=='__main__':main()
