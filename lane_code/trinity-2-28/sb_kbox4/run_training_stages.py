"""Run registered CPU stages with all children confined to eight local CPU cores."""
import hashlib,json,os,subprocess,sys,time
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
        saved=ROOT/'out/box_ladder/nonull/TRAIN_OOF.json'
        if saved.exists():
            meta=json.loads(saved.read_text());assert len(meta['records'])==5
            for name in ['train_nonull_v2.py','selector_nonull.py']:
                p=ROOT/name;assert meta['input_sha256'][str(p)]==hashlib.sha256(p.read_bytes()).hexdigest()
            for k in range(5):
                p=saved.parent/f'fold_{k}.safetensors'
                assert meta['input_sha256'][str(p)]==hashlib.sha256(p.read_bytes()).hexdigest()
            print('Verified and reused all five completed selector folds',flush=True)
        else:run(['train_nonull_v2.py'],'nonull.log')
        shards('extras');run(['summarize_train.py','final'],'summary.log')
    else:raise ValueError(stage)

if __name__=='__main__':main()
