"""Run registered CPU stages with all children confined to eight local CPU cores."""
import json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:8])

def run(args,log):
    with (ROOT/'out'/log).open('w') as f:
        result=subprocess.run(['nice','-n','10',sys.executable,'-B',*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    print(json.dumps(dict(command=args,returncode=result.returncode,log=log)),flush=True)
    if result.returncode:raise SystemExit(result.returncode)

def shards(phase):
    jobs=[]
    for k in range(4):
        f=(ROOT/'out'/f'{phase}_{k}.log').open('w')
        p=subprocess.Popen(['nice','-n','10',sys.executable,'-B','train_pricing.py',phase,str(k),'4'],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        jobs.append((p,f,k))
    # On an ordinary failure, let other assigned shards finish; never kill or relaunch.
    failed=[]
    for p,f,k in jobs:
        code=p.wait();f.close();print(json.dumps(dict(phase=phase,shard=k,returncode=code)),flush=True)
        if code:failed.append(code)
    if failed:raise SystemExit(failed[0])

def main():
    assert json.loads((ROOT/'out/box_ladder/REFERENCE_REBUILD.json').read_text())['status']=='PASS'
    stage=sys.argv[1]
    if stage=='dry':
        run(['train_pricing.py','dry'],'dry_pricing.log')
        run(['validate_dry.py'],'dry_validation.log')
        assert json.loads((ROOT/'out/DRYRUN.json').read_text())['status']=='PASS'
    elif stage=='base':
        shards('base');run(['summarize_train.py','freeze'],'freeze.log')
    elif stage=='extras':
        run(['train_nonull_v2.py'],'nonull.log');shards('extras');run(['summarize_train.py','final'],'summary.log')
    else:raise ValueError(stage)

if __name__=='__main__':main()
