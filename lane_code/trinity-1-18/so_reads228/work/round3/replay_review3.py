"""Replay every supplied round-three return without editing reviewer evidence."""
import argparse,json,sys
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--kit',required=True);parser.add_argument('--out',required=True)
a=parser.parse_args();kit=Path(a.kit).resolve();sys.path.insert(0,str(kit))
import compare228 as Q
from common228 import read,write,utc,Refusal
L=Path('/scratch/jjyeung/orch_n30/so_reads228');output=Path(a.out);output.mkdir(parents=True,exist_ok=True)
fixed=read(kit/'FIRST50.json');rows=[]
for root in sorted((L/'work/review_tests_cr3').iterdir()):
    candidate=root/'ret'
    if not candidate.is_dir():continue
    try:
        result=Q.compare(kit/'reference',candidate,first50=fixed)
        write(output/(root.name+'.json'),result)
        summary={k:result[k] for k in ('verdict','eligible','identical','ineligibility_reasons')}
    except (Refusal,ValueError,KeyError,OSError) as error:
        summary=dict(verdict='REFUSED',error=str(error))
    rows.append(dict(probe=root.name,**summary))
record=dict(utc=utc(),kit=str(kit),probes=rows)
write(output/'PROBES.json',record);print(json.dumps(record,sort_keys=True,indent=2))
