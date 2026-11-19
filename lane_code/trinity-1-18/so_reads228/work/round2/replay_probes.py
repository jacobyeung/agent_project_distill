"""Replay the supplied reviewer fixtures without editing them."""
import argparse
import json
from pathlib import Path
import sys

parser=argparse.ArgumentParser()
parser.add_argument('--kit',required=True);parser.add_argument('--out',required=True)
args=parser.parse_args();kit=Path(args.kit).resolve();sys.path.insert(0,str(kit))
import compare228 as Q
from common228 import read,write,utc
L=Path('/scratch/jjyeung/orch_n30/so_reads228');probes=L/'work/review_tests'
fixed=read(L/'work/round2/kit/FIRST50.json');output=Path(args.out);output.mkdir(parents=True,exist_ok=True)
results=[];used=set()
for directory in sorted(probes.glob('cr2probe*')):
    candidate=directory/'ret'
    if not candidate.is_dir():continue
    reference=(probes/'cr2probek3q1gfoz/ref') if directory.name=='cr2probexe5qlhqd' else kit/'reference'
    used.add(directory.name)
    if reference.name=='ref':used.add(reference.parent.name)
    result=Q.compare(reference,candidate,first50=fixed)
    write(output/(directory.name+'.json'),result)
    result={k:result[k] for k in ('verdict','eligible','identical','ineligibility_reasons')}
    results.append(dict(probe=directory.name,reference=str(reference),**result))
record=dict(utc=utc(),kit=str(kit),probe_directories=sorted(used),comparisons=results)
write(output/'PROBES.json',record);print(json.dumps(record,indent=2,sort_keys=True))
assert used=={p.name for p in probes.glob('cr2probe*')}
