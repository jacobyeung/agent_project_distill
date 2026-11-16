"""Dry-bind every boundary template; no weights, frames, network or GPU are read."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *

def main():
    p=argparse.ArgumentParser();p.add_argument('--dest',required=True);args=p.parse_args()
    dest=local(args.dest);dest.mkdir(parents=True,exist_ok=False)
    original=load(ROOT/'work/dry_m100_main/request.json');models=dest/'models.json';dump(models,original['models'])
    kit='/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3/aws_vl64rt'
    export=original['models']['cp1m200']['path'];frames=original['devs1']['frames_root'];cells=[]
    for step in (100,200):
        for family in ('main','away','forward'):
            name=f'm{step}_{family}';d=dest/name
            cmd=[sys.executable,'-I','-s',str(ROOT/'out/direct.py'),'bind','--step',str(step),'--family',family,
                '--export',export,'--sha256',PARENT_SHA,'--models',str(models),'--kit',kit,'--frames-root',frames,
                '--dest',str(d),'--dry','--parent-standin']
            r=subprocess.run(cmd,capture_output=True,text=True)
            (dest/(name+'.log')).write_text(r.stdout+r.stderr)
            if r.returncode:raise RuntimeError(name+' failed: '+r.stderr[-2000:])
            cells.append(dict(name=name,kind='direct',family=family,step=step,request=pin(d/'request.json'),dry=True))
        for scope,arms in [('supported600',('forced_route','scripted','forced_direct','unflagged')),
                           ('main1525',('forced_route','forced_direct','unflagged'))]:
            for arm in arms:
                name=f'm{step}_{scope}_{arm}';d=dest/name
                cmd=[sys.executable,'-I','-s',str(ROOT/'out/routed.py'),'bind','--step',str(step),'--arm',arm,'--scope',scope,
                    '--export',export,'--sha256',PARENT_SHA,'--frames-root',frames,'--dest',str(d),'--dry','--parent-standin']
                r=subprocess.run(cmd,capture_output=True,text=True);(dest/(name+'.log')).write_text(r.stdout+r.stderr)
                if r.returncode:raise RuntimeError(name+' failed: '+r.stderr[-2000:])
                cells.append(dict(name=name,kind='routed',arm=arm,scope=scope,step=step,request=pin(d/'request.json'),dry=True))
    dump(dest/'CELLS.json',dict(cells=cells,count=len(cells),parent_sha256=PARENT_SHA,export_bytes_verified=False,
        omissions={'scripted_main1525':'Native scripted API supports only 600 items; this bind must refuse.'}))
    print(json.dumps(dict(passed=len(cells),cells=str(dest/'CELLS.json'),scope='metadata-only parent dry binds')))
if __name__=='__main__':main()
