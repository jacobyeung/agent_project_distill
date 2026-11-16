"""Invoke the unchanged reviewed export admission after a sealed receipt check."""
import argparse
from pathlib import Path
import sys
from types import SimpleNamespace as NS
sys.path.insert(0, str(Path(__file__).resolve().parent))
from guard_core import parse_done, read, verify_archive, write

def stage(root, archive, done_path, step, expected, reviewed):
    raw=Path(done_path).read_bytes()
    done=parse_done(raw,'359fcc3c',step)
    if done!=expected:raise ValueError('Completion record changed after packet preparation')
    verify_archive(archive,done)
    # The reviewed function expects JSON. Its plain-text parser and extraction/checker remain unchanged.
    if reviewed.parse_done(raw,'359fcc3c',step)!=done:
        raise ValueError('Reviewed completion parser disagrees')
    normalized=Path(root)/'candidate_done.json'
    write(normalized,done)
    return reviewed.stage_export(NS(root=str(root),run='359fcc3c',step=step,tar=str(archive),
        done=str(normalized),full=True,bwrap=str(Path(root)/'bwrap')))

def main():
    p=argparse.ArgumentParser()
    for name in ('root','archive','done','expected'):p.add_argument('--'+name,required=True)
    p.add_argument('--step',required=True,type=int)
    a=p.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parent/'reviewed'))
    import export_stage
    result=stage(a.root,a.archive,a.done,a.step,read(a.expected),export_stage)
    write(Path(a.root)/'CANDIDATE_STAGE.json',result)
if __name__=='__main__':main()
