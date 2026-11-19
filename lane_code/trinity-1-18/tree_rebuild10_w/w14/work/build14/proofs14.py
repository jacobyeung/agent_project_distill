from pathlib import Path
import subprocess,sys,json,time,os
L=Path(__file__).resolve().parents[2];B=L/'work/build14';runs=[]
tasks=json.loads((B/'TASKS.json').read_text())
if len(sys.argv)>1:
    start=next(i for i,(name,args) in enumerate(tasks) if name==sys.argv[1])
    names={name for name,args in tasks[:start]}
    runs=[r for r in json.loads((B/'PROOF_RUNS.json').read_text()) if r['name'] in names]
    assert all(r['returncode']==0 for r in runs)
    tasks=tasks[start:]
for name,args in tasks:
    env=dict(os.environ,B14_PROOF=name)
    out=B/'proofs'/name;out.mkdir(parents=True,exist_ok=True)
    start=time.time()
    with (out/'console.log').open('w') as f:r=subprocess.run([sys.executable,'-I','-s','-B',str(B/args[0]),*args[1:]],env=env,stdout=f,stderr=subprocess.STDOUT)
    runs.append(dict(name=name,returncode=r.returncode,seconds=time.time()-start))
    (B/'PROOF_RUNS.json').write_text(json.dumps(runs,indent=2))
    print(name,r.returncode,flush=True)
    (B/'STATUS.md').write_text('# Build 14 status\n\nGO=false. Real A/C configs refuse routing_opener_init; the native initializer changes weights under reset. Scale and absolute milestone changes are implemented. Last proof: '+name+', exit '+str(r.returncode)+'. See PROOF_RUNS.json. Final qualification remains.\n')
    if r.returncode:raise SystemExit('Proof failed; no automatic retry: '+name)
