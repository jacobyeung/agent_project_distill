"""Compare two local return inventories using paired physical-room bootstrap."""
import argparse
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'readk'))
from room_bootstrap import paired
from f1f2 import F1_TYPES

FAMILIES=('main','away','forward','r0dev')

def load(paths):
    return [json.loads(line) for p in paths for line in Path(p).read_text().splitlines() if line.strip()]

def index(rows,step):
    found={}
    for r in rows:
        r=dict(r,family='r0dev' if r['family']=='a7' else r['family'])
        key=(r['family'],r['id'])
        if r['family'] not in FAMILIES or key in found:
            raise ValueError('Unknown family or duplicate item')
        if (type(r['step']) is not int or r['step']!=step or r['budget']!=2048 or
                type(r['score']) not in (int,float) or not math.isfinite(r['score']) or
                not 0<=r['score']<=1 or not r.get('room') or not r.get('scene')):
            raise ValueError('Invalid scored item or step')
        found[key]=r
    return found

def compare(d0,h1,step):
    if step not in (100,200):raise ValueError('Pair only matching registered milestones')
    a,b=index(d0,step),index(h1,step)
    shared=set(a)&set(b)
    if not shared:raise ValueError('No shared items')
    for key in sorted(shared):
        for field in ('task_type','room','scene','scoring_basis','level','pair_id','count_kind'):
            if a[key].get(field)!=b[key].get(field):
                raise ValueError('Paired metadata differs: '+field)
    def convert(r):
        return dict(key=r['id'],room=r['room'],question_type=r['task_type'],stratum='paired',scores={'value':r['score']})
    result=dict(step=step,direction='H1-1 minus D0',budget=2048,replicates=10000,seed=20261115,
        shared_items=len(shared),d0_only=len(set(a)-shared),h1_only=len(set(b)-shared),families={},harm=[])
    for family in FAMILIES:
        keys=sorted(k for k in shared if k[0]==family)
        if not keys:continue
        per_type={}
        for task in sorted({a[k]['task_type'] for k in keys}):
            subset=[k for k in keys if a[k]['task_type']==task]
            value=paired([convert(b[k]) for k in subset],[convert(a[k]) for k in subset],
                         'value',replicates=10000,seed=20261115)
            value['f1_registered']=task in F1_TYPES
            value['harm']=task in F1_TYPES and value['ci95_pp'][1]<0
            if value['harm']:result['harm'].append(dict(family=family,task_type=task))
            per_type[task]=value
        result['families'][family]=per_type
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--d0',nargs='+',required=True);p.add_argument('--h1',nargs='+',required=True)
    p.add_argument('--step',type=int,choices=(100,200),required=True);p.add_argument('--output',required=True)
    a=p.parse_args(); result=compare(load(a.d0),load(a.h1),a.step)
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps(dict(shared_items=result['shared_items'],harm=result['harm'])))

if __name__=='__main__':main()
