from pathlib import Path
import hashlib,json,os,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';steps=[]
for name in ('mutation_confirm','make_delivery','package','delivery_receipts','finish_report'):
    command=[sys.executable,'-I','-s','-B',str(B/(name+'.py'))]
    if name=='package':command.append(str(L/json.loads((B/'DELIVERY.json').read_text())['path']))
    (B/'STATUS.md').write_text('CPU coverage gaps and R2 failures are zero; BF16 parity is the sole regression. Final delivery step: '+name+'. GO=false. Evidence: GAPS.json, SUITE_COMPARISON.json, FINAL_REFRESH.json.\n')
    start=time.time()
    with (B/('final_'+name+'.log')).open('w') as stream:
        code=subprocess.run(command,cwd=L,env=os.environ,stdout=stream,stderr=subprocess.STDOUT).returncode
    record=dict(step=name,returncode=code,seconds=time.time()-start,
        script_sha256=hashlib.sha256((B/(name+'.py')).read_bytes()).hexdigest())
    steps.append(record);(B/'FINAL_REFRESH.json').write_text(json.dumps(steps,indent=2))
    print(json.dumps(record),flush=True)
    if code<0:raise SystemExit('A process was killed; stop without retry.')
    if code:raise SystemExit('Final delivery step failed: '+name)
