"""Orchestrator-only GPU entry point: one model load, pilot estimates, global time cap."""
import argparse
import json
import time
from pathlib import Path
from .io import dump, rows
from .run import run, plan
from .model import HFBackend


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--checkpoint',required=True);p.add_argument('--dev-candidates',required=True)
    p.add_argument('--pointing-candidates');p.add_argument('--out',required=True)
    p.add_argument('--phase',choices=['pilot','finish'],default='pilot');p.add_argument('--batch-size',type=int,default=4)
    p.add_argument('--stage',choices=['decisive','boxes','pointing'],default='decisive')
    p.add_argument('--max-seconds',type=float,required=True,help='Orchestrator assigns remaining share of the combined <=10800-second GPU budget.')
    p.add_argument('--device',default='cuda');a=p.parse_args()
    if a.max_seconds<=120:p.error('Require a budget greater than 120 seconds')
    root=Path(a.out);root.mkdir(parents=True,exist_ok=True)
    calls=[]
    for dataset,path in [('dev',a.dev_candidates),('pointing',a.pointing_candidates)]:
        if path is None:continue
        if (a.stage=='pointing') != (dataset=='pointing'):continue
        for form in (['V3'] if a.stage=='boxes' else ['V1','V2']):
            count=len(plan(rows(path),form))
            calls.append(dict(dataset=dataset,path=path,form=form,count=count))
    started=time.monotonic();backend=HFBackend(a.checkpoint,a.device);reports=[]
    for job in calls:
        remaining=a.max_seconds-(time.monotonic()-started)-120
        if remaining<=0:break
        args=argparse.Namespace(checkpoint=a.checkpoint,candidates=job['path'],form=job['form'],
            out=str(root/(job['dataset']+'_'+job['form']+'.jsonl')),batch_size=a.batch_size,
            variant='outline',stub=False,device=a.device,limit=256 if a.phase=='pilot' else None,
            dry_run=False,max_seconds=remaining)
        reports.append(dict(job,report=run(args,backend)))
        if time.monotonic()-started>=a.max_seconds-120:break
    estimates=[]
    for job in calls:
        output=root/(job['dataset']+'_'+job['form']+'.jsonl')
        n_done=len({r['request_id'] for r in rows(output)}) if output.exists() else 0
        pilot=Path(str(output)+'.pilot256.json');runfile=Path(str(output)+'.run.json')
        if pilot.exists():
            measured=json.loads(pilot.read_text());rate=measured['calls_per_second']
        elif runfile.exists():
            measured=json.loads(runfile.read_text());rate=measured['completed_this_run']/max(measured['seconds'],1e-9)
        else:rate=None
        estimates.append(dict(job,done=n_done,remaining=job['count']-n_done,calls_per_second=rate,
            estimated_remaining_seconds=(job['count']-n_done)/rate if rate else None))
    known=all(x['estimated_remaining_seconds'] is not None for x in estimates)
    report=dict(phase=a.phase,stage=a.stage,checkpoint=a.checkpoint,wall_seconds=time.monotonic()-started,
        assigned_budget_seconds=a.max_seconds,calls=sum(x['count'] for x in calls),jobs=estimates,
        estimated_remaining_seconds=sum(x['estimated_remaining_seconds'] for x in estimates) if known else None,
        instruction='Sum both checkpoint pilots, model loads, and remaining projections before assigning finish budgets; combined GPU wall time must be <=10800 seconds.')
    dump(root/('SUITE_'+a.stage.upper()+'_'+a.phase.upper()+'.json'),report);print(json.dumps(report))

if __name__=='__main__':main()
